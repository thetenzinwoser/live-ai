import threading
import pyaudio
from google.cloud import speech
from openai import OpenAI

# Initialize OpenAI API
def load_api_key(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()  # Remove any surrounding whitespace or newlines
    except FileNotFoundError:
        print(f"Error: API key file not found at {file_path}.")
        exit(1)
    except Exception as e:
        print(f"Error loading API key: {e}")
        exit(1)

client = OpenAI(api_key=load_api_key("openai_key.txt"))


# Analyze the transcription with GPT
def analyze_with_gpt(transcription, query):
    """Send the transcription and user query to OpenAI GPT for analysis."""
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping with meeting discussions."},
            {"role": "user", "content": f"Here is the meeting transcription so far: {transcription}. The user has a question: '{query}'. Please provide a response."}
        ])
        # Extract GPT's response (updated syntax)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        return f"Error generating feedback: {e}"



def transcribe_streaming():
    # Initialize the Speech client
    client = speech.SpeechClient()

    # Audio stream config
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # Set up microphone input
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)

    print("Listening... Press Ctrl+C to stop.")

    def generator():
        while True:
            yield stream.read(1024)

    # Send audio chunks to Google Cloud and get responses
    requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in generator())
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    transcription = ""  # To accumulate transcriptions

    # Process responses in real-time
    for response in responses:
        for result in response.results:
            transcript = result.alternatives[0].transcript
            transcription += transcript + " "

            # Save transcription to a file
            with open("live_transcription.txt", "a") as f:
                f.write(transcript + "\n")

            # Print the transcription to the console
            print("Transcript: ", transcript)

def handle_user_queries():
    """Continuously listen for user queries and process them with GPT."""
    transcription_file = "live_transcription.txt"

    while True:
        query = input("\nType your query (or type 'exit' to stop querying): ")
        if query.lower() == "exit":
            print("Exiting query system.")
            break

        # Load the latest transcription
        try:
            with open(transcription_file, "r") as f:
                transcription = f.read()
        except FileNotFoundError:
            print("Transcription file not found yet.")
            continue

        # Analyze the query with GPT
        feedback = analyze_with_gpt(transcription, query)
        print("\n--- GPT Feedback ---")
        print(feedback)
        print("--------------------")

if __name__ == "__main__":
    # Run transcription and user query handling in parallel
    try:
        transcription_thread = threading.Thread(target=transcribe_streaming)
        query_thread = threading.Thread(target=handle_user_queries)

        transcription_thread.start()
        query_thread.start()

        transcription_thread.join()
        query_thread.join()
    except KeyboardInterrupt:
        print("\nStopped.")
