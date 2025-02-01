import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_gpt_response(question, context=""):
    """
    Get a response from GPT for chat messages, incorporating meeting context when available.
    """
    try:
        messages = [
            {
                "role": "system", 
                "content": """You are Pai, an AI assistant helping with meeting discussions. 
                You have access to the live meeting transcription and can reference it to provide context-aware responses.
                Use Markdown formatting for better readability:
                - ## for headers
                - * for bullet points
                - ` for code
                - ** for emphasis
                
                Keep responses concise but informative. If referencing the meeting, cite specific parts.
                If there's no meeting context or the question is unrelated, respond generally but helpfully."""
            }
        ]

        # Add context if available
        if context.strip():
            messages.append({
                "role": "system",
                "content": f"Here is the current meeting transcription for context:\n{context}"
            })

        # Add user question
        messages.append({
            "role": "user",
            "content": question
        })

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in get_gpt_response: {e}")
        return f"I apologize, but I encountered an error while processing your request. Please try again."


# THIS IS FOR THE QUESTION AND ANSWER SECTION
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

# THIS IS FOR THE MEETING MINUTES
def generate_meeting_minutes(transcription):
    """Generate meeting minutes summary from the transcription."""
    try:
        # First process the long transcription into a rolling summary
        summary = process_long_transcription(transcription)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that creates concise meeting minutes from transcriptions. Use as little words as possible. Organize the meeting minutes chronologically. Use Markdown formatting: ## for headers, 1. for numbered lists, - [ ] for unchecked boxes, - [x] for checked boxes, * for bullet points, and ** for emphasis."},
                {"role": "user", "content": f"Please create meeting minutes from this meeting summary, highlighting the main points discussed: {summary}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating meeting minutes: {e}"


################################################################################

# THIS IS FOR THE ROLLING SUMMARY
def chunk_transcription(transcription, chunk_size=200):  # Reduced chunk size for testing
    """Split transcription into manageable chunks."""
    # Remove empty lines and normalize whitespace
    cleaned_text = "\n".join(line.strip() for line in transcription.split("\n") if line.strip())
    return [cleaned_text[i:i + chunk_size] for i in range(0, len(cleaned_text), chunk_size)]

def summarize_chunk(chunk):
    """Summarize a single chunk of the transcription."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant that creates very concise summaries of meeting segments. Use as few words as possible while capturing key points."},
                {"role": "user", "content": f"Summarize this part of the meeting concisely:\n{chunk}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing chunk: {e}"

def process_long_transcription(transcription):
    """Process a long transcription using rolling summaries."""
    chunks = chunk_transcription(transcription)
    rolling_summary = []
    
    for chunk in chunks:
        if not chunk.strip():  # Skip empty chunks
            continue
        # Summarize current chunk
        chunk_summary = summarize_chunk(chunk)
        # Append to rolling summary list if not an error
        if not chunk_summary.startswith("Error summarizing chunk"):
            rolling_summary.append(chunk_summary)
    
    # Join all summaries with newlines
    return "\n".join(rolling_summary) if rolling_summary else "No valid summaries generated."