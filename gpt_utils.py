import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function to interact with OpenAI for a question and transcription context
def analyze_with_gpt(transcription, query):
    """Send transcription and query to OpenAI for analysis."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant helping with meeting discussions."},
                {"role": "user", "content": f"Here is the meeting transcription so far: {transcription}. The transcription is live and ongoing. The confidence score indicates AI accuracy, with 1 being most confident. Lower scores suggest potential inaccuracies. The user has a question: '{query}'. Please provide a response."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating feedback: {e}"
    

    

def get_gpt_response(question, context=""):
    """
    Wrapper function to make it easier to query GPT with a question
    and optional context (like transcription).
    """
    try:
        response = analyze_with_gpt(context, question)
        return response
    except Exception as e:
        return f"Error processing question: {e}"

def generate_action_items(transcription):
    """Generate action items from the transcription."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that identifies and extracts action items from meeting transcriptions. Format each action item on a new line with a bullet point."},
                {"role": "user", "content": f"Please analyze this meeting transcription and list all action items, tasks, and commitments mentioned: {transcription}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating action items: {e}"
