import logging
import os
from datetime import datetime
import sqlalchemy
from dotenv import load_dotenv
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

from extraction import (
    extract_callback_number,
    extract_is_patient,
    extract_date_of_birth,
    extract_gender,
    extract_state,
    extract_symptom,
)
from prompt import questions, extract_yes_or_no

db = SQLAlchemy()
error_counter = 0  # Initialize error_counter globally
current_question_index = 0  # Initialize current_question_index globally

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Get database connection details from environment variables
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    db_host= os.getenv("DB_PUBLIC_IP")
    instance_unix_socket = os.getenv("INSTANCE_UNIX_SOCKET")
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_uri = sqlalchemy.engine.url.URL.create(
        drivername="mysql+pymysql",
        username=db_user,
        password=db_pass,
        database=db_name,
        query={"unix_socket": instance_unix_socket},
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    # Construct the Cloud SQL connection URI using the public IP address
    # Logging the URI (remove or obfuscate sensitive information in production)
    logging.info(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


    class Call(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        caller_sid = db.Column(db.String(120), unique=True, nullable=False)
        callback_number = db.Column(db.String(120), nullable=True)
        is_patient = db.Column(db.String(10), nullable=True)
        date_of_birth = db.Column(db.String(10), nullable=True)
        gender = db.Column(db.String(10), nullable=True)
        state = db.Column(db.String(16), nullable=True)
        symptom = db.Column(db.String(255), nullable=True)
        call_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        confirmation_status = db.Column(db.String(10), nullable=True)


    expected_responses = [ # List of validation functions
        extract_callback_number,
        extract_is_patient,
        extract_date_of_birth,
        extract_gender,
        extract_state,
        extract_symptom
    ]

    question_to_column = {
        0: 'callback_number',
        1: 'is_patient',
        2: 'date_of_birth',
        3: 'gender',
        4: 'state',
        5: 'symptom'
    }
    twilio_account_sid= os.getenv('ACCOUNT_SID')
    twilio_auth_token= os.getenv('TWILIO_AUTH_TOKEN')

    client = Client(twilio_account_sid, twilio_auth_token) # Twilio Client


    @app.route('/')
    def index():
        return "Hello from my Flask app! Waiting for a call!"

    @app.route("/answer", methods=["POST"])  # Answers the incoming call.
    def answer_call():
        caller_sid = request.form.get('CallSid')
        new_call = Call(caller_sid=caller_sid)
        db.session.add(new_call)
        db.session.commit()
        logging.info("Incoming call received")
        response = VoiceResponse() # create Twilio voice to interact with caller
        response.say("Hello, let’s collect some information to expedite your call.", voice="en-US-Neural2-J")
        response.redirect("/ask?CallSid=" + caller_sid)
        return str(response)

    @app.route("/ask", methods=["POST"]) # Asks the current question.
    def ask_question():
        global current_question_index, error_counter
        try:
            caller_sid = request.form.get('CallSid')
            if error_counter > 2:
                logging.info("Error count exceeded limit, transferring to agent.")
                response = VoiceResponse()
                response.say("There seems to be some issues. Please hold while we transfer you to an agent.", voice="en-US-Neural2-J")
                response.redirect("/transfer?CallSid=" + caller_sid)
                call = Call.query.filter_by(caller_sid=caller_sid).first()
                if call:
                    column = question_to_column.get(current_question_index, None)
                    if column:
                        setattr(call, column, "Call issue: too many errors")
                    db.session.commit()
                return str(response)
            if current_question_index < len(questions):
                logging.info(f"Asking question {current_question_index + 1}: {questions[current_question_index]}")
                response = VoiceResponse()
                if current_question_index == 0:
                    gather = Gather(input='dtmf speech', action='/transcribe?CallSid=' + caller_sid, method='POST', numDigits='10', speechModel="phone_call", enhanced="true")
                    gather.say(questions[current_question_index], voice="en-US-Neural2-J")
                    response.append(gather)
                    return str(response)
                if current_question_index == 2:
                    gather = Gather(input='dtmf speech', action='/transcribe?CallSid=' + caller_sid, method='POST', speechModel="phone_call", enhanced="true")
                    gather.say(questions[current_question_index], voice="=en-US-Neural2-J")
                    response.append(gather)
                    return str(response)
                gather = Gather(input='speech', action='/transcribe?CallSid=' + caller_sid, method='POST', speechModel="phone_call", enhanced="true")
                gather.say(questions[current_question_index], voice="en-US-Neural2-J")
                response.append(gather)
                return str(response)
            response = VoiceResponse()
            response.say("Thank you for your responses, you will now be transferred to a agent. Goodbye!", voice="en-US-Neural2-J")
            return str(response)
        except Exception as e:
            logging.error(f"Error in ask_question: {e}")
            return str(e), 500

    @app.route("/transcribe", methods=["POST"]) # Endpoint to receive audio stream from Twilio and send it to Deepgram for transcription.
    def transcribe():
        global current_question_index, error_counter
        try:
            caller_sid = request.args.get('CallSid')
            logging.info("Starting transcription process")
            logging.info(f"Request form data: {request.form}")
            speech_result = request.form.get('SpeechResult')
            digits_result = request.form.get('Digits')
            logging.info(f"Received transcription: {speech_result}")

            if not speech_result and not digits_result:
                logging.error("No SpeechResult found in the request.")
                return Response("No SpeechResult found", status=400)

            user_response = speech_result if speech_result else digits_result
            call = Call.query.filter_by(caller_sid=caller_sid).first()
            if call:
                column = question_to_column.get(current_question_index, None)
                if column:
                    question_and_response = f"{questions[current_question_index]} {user_response}"
                    setattr(call, column, question_and_response)
                db.session.commit()

            buffer = getattr(call, column, None)
            logging.info(f"Buffer content: {buffer}")

            validation_function = expected_responses[current_question_index]
            extracted_info = validation_function(buffer)
            logging.info(f"Extracted info for question {current_question_index + 1}: {extracted_info}")

            if extracted_info is not None:
                logging.info(f"Valid response received: {extracted_info}")
                setattr(call, column, extracted_info)
                db.session.commit()

                if current_question_index == 0:
                    response = VoiceResponse()
                    response.say(f"You said your callback number is {extracted_info}. Press one to confirm or two if incorrect?", voice="en-US-Neural2-J")
                    gather = Gather(input='dtmf speech', action='/confirm?CallSid=' + caller_sid, method='POST', speechModel="phone_call", numDigits="1", enhanced="true")
                    response.append(gather)
                    return str(response)
                else:
                    current_question_index += 1
                    return ask_question()
            else:
                logging.info("Invalid response. Repeating the question.")
                response = VoiceResponse()
                response.say("Sorry I didn't catch that.", voice="en-US-Neural2-J")
                if column:
                    setattr(call, column, None)
                db.session.commit()
                error_counter += 1
                return ask_question()
        except Exception as e:
            logging.error(f"Error in transcribe: {e}")
            return str(e), 500

    @app.route("/confirm", methods=["POST"])  # Handles the confirmation of the callback number.
    def confirm():
        global current_question_index, error_counter
        caller_sid = request.args.get('CallSid')
        logging.info("Starting confirmation process")
        logging.info(f"Request form data: {request.form}")
        digits_result = request.form.get('Digits')
        logging.info(f"Received DTMF: {digits_result}")
        confirmation_result = request.form.get('SpeechResult')
        logging.info(f"Received confirmation: {confirmation_result}")

        if not confirmation_result and not digits_result:
            logging.error("No SpeechResult found in the request.")
            return Response("No SpeechResult found", status=400)

        confirmation_valid= extract_yes_or_no(digits_result)
        call = Call.query.filter_by(caller_sid=caller_sid).first()
        if call:
            call.confirmation_status = confirmation_valid
            db.session.commit()

        if confirmation_valid and confirmation_valid.lower() == "yes":
            current_question_index += 1
            return ask_question()
        else:
            logging.info("Invalid confirmation. Repeating the question.")
            error_counter += 1
            return ask_question()

    @app.route("/transfer", methods=["POST"]) # Transfers the caller to an agent.
    def transfer():
        caller_sid = request.args.get('CallSid')
        response = VoiceResponse()
        response.say("Please hold while we transfer you to an agent.", voice="en-US-Neural2-J")
        return str(response)

    return app

app = create_app()
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
