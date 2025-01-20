from openai import OpenAI

def load_api_key(file_path):
    """Load the OpenAI API key from a file."""
    try:
        with open(file_path, "r") as file:
            key = file.read().strip()  # Remove whitespace or newlines
            print(f"Loaded API Key: {key[:5]}...")  # Masked output for debugging
            return key
    except FileNotFoundError:
        print(f"Error: API key file not found at {file_path}.")
        exit(1)
    except Exception as e:
        print(f"Error loading API key: {e}")
        exit(1)

client = OpenAI(api_key=load_api_key("openai_key.txt"))
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
