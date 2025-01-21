from flask import Flask, render_template, request, jsonify
from threading import Thread
from speech_utils import transcribe_streaming
from gpt_utils import analyze_with_gpt

app = Flask(__name__)

# Shared variables to hold transcription and status
transcription_data = []
is_transcribing = False

@app.route('/')
def index():
    """Render the main web page."""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_transcription():
    """Start the transcription process."""
    global is_transcribing
    if not is_transcribing:
        is_transcribing = True
        thread = Thread(target=run_transcription)
        thread.start()
        return jsonify({"message": "Transcription started!"})
    return jsonify({"message": "Transcription is already running!"})

@app.route('/stop', methods=['POST'])
def stop_transcription():
    """Stop the transcription process."""
    global is_transcribing
    is_transcribing = False
    return jsonify({"message": "Transcription stopped!"})

@app.route('/data', methods=['GET'])
def get_data():
    """Get the live transcription data."""
    print("Returning transcription data:", transcription_data)  # Debug log
    return jsonify({"transcription": transcription_data})


def run_transcription():
    """Run the transcription process and update the transcription_data."""
    global transcription_data, is_transcribing
    transcription_data = []  # Clear existing data
    print("Starting transcription...")
    for line in transcribe_streaming():  # Ensure `transcribe_streaming` yields lines
        if not is_transcribing:
            break
        transcription_data.append(line)
        print("Updated transcription data:", transcription_data)  # Debug log


if __name__ == "__main__":
    app.run(debug=True)
