import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Set OpenAI API key globally

def analyze_with_gpt(transcription, query):
    """Send transcription and query to OpenAI for analysis."""
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping with meeting discussions."},
            {"role": "user", "content": f"Here is the meeting transcription so far: {transcription}. The user has a question: '{query}'. Please provide a response."}
        ])
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating feedback: {e}"
