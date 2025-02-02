import sounddevice as sd
from google.cloud import speech
import os
import re
from gpt_utils import generate_meeting_minutes
import json
from events import notify_frontend_update
import threading
import time
from gpt_utils import get_gpt_response

# Set start method for multiprocessing
if __name__ == "__main__":
    os.set_start_method("spawn")

# Global variables for in-memory transcription
class TranscriptionState:
    def __init__(self):
        self.transcriptions = []
        self.recent_transcriptions = []
        self.last_saved_segment = ""
        self.should_continue = threading.Event()
        self.start_time = None

# Dictionary to store per-user transcription states
user_states = {}

def get_user_state(user_dir):
    """Get or create transcription state for a user"""
    if user_dir not in user_states:
        user_states[user_dir] = TranscriptionState()
    return user_states[user_dir]

def save_transcription_to_file(user_dir, transcription):
    """Append the latest transcription to the user's file."""
    filepath = os.path.join(user_dir, "live_transcription.txt")
    with open(filepath, "a") as f:
        f.write(transcription + "\n")

def save_question_and_answer(user_dir, question, answer):
    """Save detected questions and their GPT answers to a user's JSON file."""
    filepath = os.path.join(user_dir, "questions_answers.json")
    try:
        with open(filepath, "r") as file:
            qa_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        qa_data = []

    state = get_user_state(user_dir)
    # Extract timestamp from the transcription line containing the question
    timestamp = "00:00"
    for line in state.transcriptions:
        if question in line:
            match = re.search(r'\(Time Stamp: (\d{2}:\d{2})\)', line)
            if match:
                timestamp = match.group(1)
                break

    qa_data.insert(0, {
        "question": question,
        "answer": answer,
        "timestamp": timestamp
    })

    with open(filepath, "w") as file:
        json.dump(qa_data, file, indent=4)

def get_full_transcription(user_dir):
    """Return all transcriptions for a user as a single string."""
    state = get_user_state(user_dir)
    return "\n".join(state.transcriptions)

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
        if line.endswith("?") or re.match(r"^(Is|What|Why|How|When|Where|Who|Do|Does|Did|Will|Would|Should|Can|Could|May|Might|Must|Should|Would|Could|May|Might|Must)\b", line, re.IGNORECASE):
            questions.append(line)
    return questions

def transcribe_streaming(user_dir):
    """Stream and transcribe audio in real-time for a specific user."""
    state = get_user_state(user_dir)
    state.should_continue.set()
    state.start_time = time.time()
    client = speech.SpeechClient()

    def record_audio():
        samplerate = 16000
        channels = 1
        dtype = 'int16'
        
        with sd.InputStream(samplerate=samplerate, channels=channels, dtype=dtype) as stream:
            while state.should_continue.is_set():
                audio_chunk, overflowed = stream.read(1024)
                if not overflowed:
                    # Convert to bytes
                    audio_data = audio_chunk.tobytes()
                    yield audio_data

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    while state.should_continue.is_set():
        try:
            print(f"Starting new session for user directory: {user_dir}")
            requests = (speech.StreamingRecognizeRequest(audio_content=chunk) 
                       for chunk in record_audio())
            responses = client.streaming_recognize(streaming_config, requests)
            process_responses(user_dir, responses)
        except Exception as e:
            print(f"Stream ended: {e}")
            if state.should_continue.is_set():
                continue
            else:
                break

def save_action_items(user_dir, action_items):
    """Save action items to a user's JSON file."""
    filepath = os.path.join(user_dir, "action_items.json")
    try:
        with open(filepath, "w") as file:
            json.dump({"action_items": action_items}, file, indent=4)
    except Exception as e:
        print(f"Error saving action items: {e}")

def save_meeting_minutes(user_dir, minutes):
    """Save meeting minutes to a user's JSON file."""
    filepath = os.path.join(user_dir, "meeting_minutes.json")
    try:
        with open(filepath, "w") as file:
            json.dump({"meeting_minutes": minutes}, file, indent=4)
    except Exception as e:
        print(f"Error saving meeting minutes: {e}")

def process_responses(user_dir, responses):
    """Handle transcription responses for a specific user."""
    state = get_user_state(user_dir)

    for response in responses:
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript
                confidence = result.alternatives[0].confidence

                elapsed_time = int(time.time() - state.start_time)
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                timestamp = f"(Time Stamp: {minutes:02d}:{seconds:02d})"

                if transcript != state.last_saved_segment:
                    state.last_saved_segment = transcript
                    formatted_line = f"{transcript} (Confidence: {confidence:.2f}) {timestamp}"
                    state.transcriptions.append(formatted_line)
                    save_transcription_to_file(user_dir, formatted_line)

                    print(f"New line added for {user_dir}: {formatted_line}")

                    questions = detect_questions(transcript)
                    for question in questions:
                        try:
                            answer = get_gpt_response(question, "\n".join(state.transcriptions))
                            save_question_and_answer(user_dir, question, answer)
                        except Exception as e:
                            print(f"Error generating answer for question '{question}': {e}")

                    try:
                        meeting_minutes = generate_meeting_minutes("\n".join(state.transcriptions))
                        save_meeting_minutes(user_dir, meeting_minutes)
                        notify_frontend_update()
                    except Exception as e:
                        print(f"Error processing updates: {e}")

def stop_transcription(user_dir):
    """Stop the transcription process for a specific user."""
    state = get_user_state(user_dir)
    state.should_continue.clear()
