import pyaudio
from google.cloud import speech
import os
import re
from gpt_utils import generate_meeting_minutes
import json
from events import notify_frontend_update
import threading
import time  # Add this import at the top
from gpt_utils import get_gpt_response

# Set start method for multiprocessing
if __name__ == "__main__":
    os.set_start_method("spawn")

# Global variables for in-memory transcription
transcriptions = []  # To store all transcriptions in memory
recent_transcriptions = []  # Cache to store recent transcriptions
CACHE_LIMIT = 10  # Limit the cache size to the last 10 phrases
last_saved_segment = ""  # To track the last saved transcription
should_continue = threading.Event()  # Add this event flag
start_time = None  # Add this variable to track start time


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

    # Extract timestamp from the transcription line containing the question
    timestamp = "00:00"
    for line in transcriptions:
        if question in line:
            # Extract timestamp using regex
            match = re.search(r'\(Time Stamp: (\d{2}:\d{2})\)', line)
            if match:
                timestamp = match.group(1)
                break

    # Insert new question at the beginning of the array
    qa_data.insert(0, {
        "question": question,
        "answer": answer,
        "timestamp": timestamp
    })

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
    """Stream and transcribe audio in real-time."""
    global start_time  # Add this line
    should_continue.set()
    start_time = time.time()  # Set the start time when transcription begins
    client = speech.SpeechClient()

    def start_stream():
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True
        )
        streaming_config = speech.StreamingRecognitionConfig(config=config)

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=16000,
                       input=True,
                       frames_per_buffer=1024)

        def generator():
            while should_continue.is_set():  # Check the flag in the generator
                yield stream.read(1024)
            # Clean up when stopped
            stream.stop_stream()
            stream.close()
            p.terminate()

        requests = (speech.StreamingRecognizeRequest(audio_content=chunk) 
                   for chunk in generator())
        return client.streaming_recognize(config=streaming_config, requests=requests)

    while should_continue.is_set():  # Check the flag in the main loop
        try:
            print("Starting new session...")
            responses = start_stream()
            process_responses(responses)
        except Exception as e:
            print(f"Stream ended: {e}")
            if should_continue.is_set():  # Only continue if not stopped
                continue
            else:
                break


def save_action_items(action_items):
    """Save action items to a JSON file."""
    try:
        with open("transcriptions/action_items.json", "w") as file:
            json.dump({"action_items": action_items}, file, indent=4)
    except Exception as e:
        print(f"Error saving action items: {e}")


def save_meeting_minutes(minutes):
    """Save meeting minutes to a JSON file."""
    try:
        with open("transcriptions/meeting_minutes.json", "w") as file:
            json.dump({"meeting_minutes": minutes}, file, indent=4)
    except Exception as e:
        print(f"Error saving meeting minutes: {e}")


def process_responses(responses):
    """Handle transcription responses and filter out duplicates."""
    global transcriptions, last_saved_segment

    for response in responses:
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence

                # Calculate timestamp
                elapsed_time = int(time.time() - start_time)
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                timestamp = f"(Time Stamp: {minutes:02d}:{seconds:02d})"

                # Filter out duplicate or repeated phrases
                if transcript != last_saved_segment:
                    last_saved_segment = transcript
                    formatted_line = f"{transcript} (Confidence: {confidence:.2f}) {timestamp}"
                    transcriptions.append(formatted_line)
                    save_transcription_to_file(formatted_line)

                    # Print the transcription to the console
                    print(f"New line added: {formatted_line}")

                    # Detect and handle questions
                    questions = detect_questions(transcript)
                    for question in questions:
                        print(f"Detected Question: {question}")
                        try:
                            answer = get_gpt_response(question, "\n".join(transcriptions))
                            print(f"Answer: {answer}")
                            save_question_and_answer(question, answer)
                        except Exception as e:
                            print(f"Error generating answer for question '{question}': {e}")

                    # Generate and save action items and meeting minutes periodically
                    try:
                        action_items = generate_action_items("\n".join(transcriptions))
                        save_action_items(action_items)
                        
                        meeting_minutes = generate_meeting_minutes("\n".join(transcriptions))
                        save_meeting_minutes(meeting_minutes)
                        
                        # Notify frontend of new content
                        notify_frontend_update()
                    except Exception as e:
                        print(f"Error processing updates: {e}")


def stop_transcription():
    """Stop the transcription process."""
    should_continue.clear()  # Clear the flag to stop the transcription
