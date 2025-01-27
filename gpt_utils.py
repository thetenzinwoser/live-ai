import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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



# Function to interact with OpenAI for a question and transcription context
def analyze_with_gpt(transcription, query):
    """Send transcription and query to OpenAI for analysis."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant helping with meeting discussions. The current meeting is being transcribed in real time. Use Markdown formatting for better readability: ## for headers, 1. for numbered lists, - [ ] for unchecked boxes, - [x] for checked boxes, * for bullet points, and ** for emphasis."},
                {"role": "user", "content": f"Here is the meeting transcription so far: {transcription}. The user has a question: '{query}'. Please provide a response using the specified Markdown formatting."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating feedback: {e}"
    

def generate_action_items(transcription):
    """Generate action items from the transcription."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that identifies and extracts action items from meeting transcriptions. The current meeting is being transcribed in real time. Use Markdown formatting: ## for headers, 1. for numbered lists, - [ ] for unchecked boxes, - [x] for checked boxes, * for bullet points, and ** for emphasis."},
                {"role": "user", "content": f"Please analyze this meeting transcription and list all action items mentioned using checkboxes and numbered lists where appropriate: {transcription}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating action items: {e}"

def generate_meeting_minutes(transcription):
    """Generate meeting minutes summary from the transcription."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that creates concise meeting minutes from transcriptions. The current meeting is being transcribed in real time. Organize the meeting minutes chronologically referencing the provided time stamps. Use Markdown formatting: ## for headers, 1. for numbered lists, - [ ] for unchecked boxes, - [x] for checked boxes, * for bullet points, and ** for emphasis."},
                {"role": "user", "content": f"Please create meeting minutes from this transcription, highlighting the main points discussed in as much detail as possible: {transcription}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating meeting minutes: {e}"
