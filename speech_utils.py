import pyaudio
from google.cloud import speech
import os
import re
from gpt_utils import get_gpt_response
import json

# Set start method for multiprocessing
if __name__ == "__main__":
    os.set_start_method("spawn")

# Global variables for in-memory transcription
transcriptions = []  # To store all transcriptions in memory
recent_transcriptions = []  # Cache to store recent transcriptions
CACHE_LIMIT = 10  # Limit the cache size to the last 10 phrases
last_saved_segment = ""  # To track the last saved transcription


def save_transcription_to_file(transcription):
    """Append the latest transcription to the file."""
    with open("transcriptions/live_transcription.txt", "a") as f:  # Use "a" mode to append
        f.write(transcription + "\n")


def save_question_and_answer(question, answer):
    """Save detected questions and their GPT answers to a JSON file."""
    try:
        with open("transcriptions/questions_answers.json", "r") as file:
            qa_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        qa_data = []

    qa_data.append({"question": question, "answer": answer})

    with open("transcriptions/questions_answers.json", "w") as file:
        json.dump(qa_data, file, indent=4)


def get_full_transcription():
    """Return all transcriptions as a single string."""
    return "\n".join(transcriptions)


def detect_questions(transcription):
    """
    Detects questions from the transcription text.

    Args:
        transcription (str): The transcription text.

    Returns:
        list: A list of detected questions.
    """
    questions = []
    for line in transcription.splitlines():
        line = line.strip()
        # Simple heuristic to detect questions
        if line.endswith("?") or re.match(r"^(What|Why|How|When|Where|Who)\b", line, re.IGNORECASE):
            questions.append(line)
    return questions


def transcribe_streaming():
    """Stream and transcribe audio in real-time without diarization."""
    client = speech.SpeechClient()

    def start_stream():
        """Inner function to start the streaming session."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True  # Enable punctuation for readability
        )
        streaming_config = speech.StreamingRecognitionConfig(config=config)

        # Set up microphone input
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024)

        def generator():
            while True:
                yield stream.read(1024)

        # Send audio chunks to Google Cloud and get responses
        requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in generator())
        return client.streaming_recognize(config=streaming_config, requests=requests)

    while True:  # Loop to restart the session
        try:
            print("Starting new session...")
            responses = start_stream()
            process_responses(responses)  # Process the transcription responses
        except Exception as e:
            print(f"Stream ended: {e}. Restarting...")
            continue  # Restart the loop to create a new session


def process_responses(responses):
    """Handle transcription responses and filter out duplicates."""
    global transcriptions, last_saved_segment  # Use global to access in-memory storage

    for response in responses:
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence

                # Filter out duplicate or repeated phrases
                if transcript != last_saved_segment:
                    last_saved_segment = transcript  # Update last saved segment
                    transcriptions.append(f"{transcript} (Confidence: {confidence:.2f})")
                    save_transcription_to_file(f"{transcript} (Confidence: {confidence:.2f})")

                    # Print the transcription to the console
                    print(f"New line added: {transcript} (Confidence: {confidence:.2f})")

                    # Detect and handle questions
                    questions = detect_questions(transcript)
                    for question in questions:
                        print(f"Detected Question: {question}")
                        try:
                            # Query GPT for an answer
                            answer = get_gpt_response(question, "\n".join(transcriptions))
                            print(f"Answer: {answer}")
                            # Save the question and answer
                            save_question_and_answer(question, answer)
                        except Exception as e:
                            print(f"Error generating answer for question '{question}': {e}")
