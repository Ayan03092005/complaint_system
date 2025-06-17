from google.cloud import dialogflow
from google.api_core.exceptions import InvalidArgument
from models import User

def process_chatbot_message(message, user_id):
    project_id = 'complaintsystembot'  # Replace with your Dialogflow project ID
    session_id = f"user-{user_id}"
    language_code = 'en'

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=message, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(
            request={'session': session, 'query_input': query_input}
        )
        fulfillment_text = response.query_result.fulfillment_text
        if response.query_result.intent.display_name == 'lodge_complaint':
            return fulfillment_text + " <a href='/submit_complaint'>Click here to lodge a complaint</a>"
        return fulfillment_text
    except InvalidArgument:
        return "Error processing your request. Please try again."
