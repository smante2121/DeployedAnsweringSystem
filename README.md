# Deployed Answering System

## Project Overview

This project is an advanced answering system designed for medical offices to handle incoming patient calls efficiently. It receives calls, gathers patient information (via voice and DTMF), uploads the data to a Google Cloud SQL instance database, and then seamlessly transfers the caller to the appropriate representative. Built using Flask and Twilio's APIs, the system is deployed on Google Cloud Run, and its deployment URL serves as the webhook for the Twilio phone number.

Upon receiving a call, the system creates a new row in the database to collect information from the caller. As the caller provides responses, either by voice or DTMF, the raw transcript is written to the appropriate cell in the database. The transcript is then analyzed to determine if a valid answer can be extracted. If valid, the transcript is replaced with a standardized answer format; otherwise, the question repeats. Logic is also incorporated to abort the call if too many errors occur. Agents can access this data instantly after the caller is transferred, streamlining the process for both patients and agents while logging call information for patient records.

This project is the culmination of three different versions, each building upon the previous one with different implementations:

- **[Version 1: STT-Gemini-TTS Web Application](https://github.com/smante2121/STT-gemini-TTS)**  
  A research-focused web application using Google's Speech-to-Text API and Gemini conversational AI to manage conversation flow, built with Flask, HTML, CSS, and JavaScript.

- **[Version 2: Desktop Answering System](https://github.com/smante2121/DesktopAnsweringSystem)**  
  A desktop application leveraging Deepgram's Speech-to-Text and Text-to-Speech APIs to manage interactions, designed as an answering system for medical offices.

- **[Version 3: Local Answering System](https://github.com/smante2121/LocalAnsweringSystem)**  
  A Python Flask application integrating Twilio's APIs for handling calls and storing caller responses in a local SQLite database, optimizing patient call management.

This final version enhances these earlier implementations, offering a robust, scalable solution for medical offices.


### Features
- **Twilio API Integration:** Manages incoming calls, gathers responses, and handles DTMF (Dual-Tone Multi-Frequency) input and voice responses through Twilio's API.
- **Cloud Deployment:** Fully deployed on Google Cloud Run, ensuring scalability, security, and reliability in handling multiple simultaneous calls.
- **Cloud SQL Integration:** Utilizes a Google Cloud MySQL instance for storing, analyzing, and finalizing call data, providing secure and scalable database management.
- **Error Handling:** Monitors and tracks errors during the response validation process, transferring the caller to a live agent if issues persist.
- **Voice Interaction:** Uses Twilio's VoiceResponse to interact with callers, asking questions and capturing their responses.

### How It Works
- **Google Cloud Run Deployment:** The application is deployed on Google Cloud Run, which allows it to scale automatically based on demand. This deployment ensures that the application is always available to handle incoming calls without the need for manual server management.
- **Database Entry:** A new row is created in the Cloud SQL database using the caller's SID (Session Identifier) when a call is received.
- **Question-Response Sequence:** The caller is asked a series of questions over the phone, and their responses are captured using Twilio's Gather feature, which accepts both DTMF input and voice responses depending on the question.
- **Data Validation:** Responses are processed using methods from `extraction.py`, validated, and then standardized before being stored in the database.

### Improvements and Further Development
- **Enhanced Transcript Management:** Implements logic to write and analyze the entire call transcript in the Cloud SQL database, associating each transcript with the respective CallSid. This enhancement improves the system's ability to manage large volumes of calls, ensuring efficient organization and retrieval of call data.
- **Deployment Optimization:** Leveraging Google Cloud Run ensures that the application can handle a large number of simultaneous calls, making it more robust and reliable for real-world use.

### Project Structure
- **app.py:** Manages the main application flow, including call handling, question-response logic, and database operations.
- **extraction.py:** Contains methods for extracting and validating responses from the caller's input.
- **prompt.py:** Contains the list of questions asked by the Twilio API during the call.
- **Dockerfile:** Used for containerizing the application for deployment on Google Cloud Run.
- **app.yaml & cloudbuild.yaml:** Configuration files used for deployment, included in the `.env` for secure management.

### Future Work
- **Extended Testing:** Conduct further testing to refine the application's performance and reliability under real-world conditions.
- **Enhanced Data Validation:** Continue to improve the validation process with additional checks and user confirmation steps.
- **Full-Scale Deployment:** After thorough testing and improvement, the system can be fully deployed for production use in medical offices or similar environments.

