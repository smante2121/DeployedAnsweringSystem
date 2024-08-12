# Deployed Answering System

## Overview
Welcome to the Deployed Answering System repository. This project is an advanced iteration of previous answering systems, now fully deployed via Google Cloud Run and utilizing a Google Cloud MySQL instance for robust data management. The system is designed to handle patient calls, collecting and validating critical information before transferring the call to an appropriate healthcare provider. It leverages Twilio's APIs for seamless voice interaction and data gathering.

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

