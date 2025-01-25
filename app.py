from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from speech_utils import transcribe_streaming
from events import socketio
import json
from gpt_utils import get_gpt_response  # Function to interact with ChatGPT
import threading

app = Flask(__name__, template_folder='templates')  # Specify the templates folder
socketio.init_app(app)
is_listening = False  # Global flag to track listening state


@app.route("/start-listening", methods=["POST"])
def start_listening():
    """Start listening for transcription and clear previous session data."""
    global is_listening

    if not is_listening:  # Prevent multiple threads
        is_listening = True

        # Clear transcription file
        with open("transcriptions/live_transcription.txt", "w") as file:
            file.write("")  # Overwrite with an empty string

        # Clear questions and answers file
        with open("transcriptions/questions_answers.json", "w") as file:
            file.write("[]")  # Overwrite with an empty JSON array

        # Clear meeting minutes file
        with open("transcriptions/meeting_minutes.json", "w") as file:
            json.dump({"meeting_minutes": ""}, file)

        # Start the transcription thread
        threading.Thread(target=transcribe_streaming).start()

        return jsonify({"message": "Listening started, previous session cleared!"})
    else:
        return jsonify({"message": "Already listening."})


@app.route("/stop-listening", methods=["POST"])
def stop_listening():
    """Stop listening for transcription."""
    global is_listening
    is_listening = False
    return jsonify({"message": "Listening stopped. Data retained until next session starts."})


@app.route('/')
def home():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    """Handle AI question requests."""
    data = request.json

    # Validate the question input
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Read transcription context
    try:
        with open("transcriptions/live_transcription.txt", "r") as file:
            context = file.read()
    except FileNotFoundError:
        context = ""
    except Exception as e:
        return jsonify({"error": f"Error reading transcription: {str(e)}"}), 500

    # Generate GPT response
    try:
        response = get_gpt_response(question, context)
        return jsonify({"answer": response})
    except Exception as e:
        # Log and return detailed error message
        return jsonify({"error": f"Error generating GPT response: {str(e)}"}), 500


@app.route('/get-questions', methods=['GET'])
def get_questions():
    """Return detected questions and their GPT answers."""
    try:
        with open("transcriptions/questions_answers.json", "r") as file:
            qa_data = json.load(file)
        return jsonify({"questions": qa_data})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"questions": []}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching questions: {str(e)}"}), 500


@app.route('/get-action-items', methods=['GET'])
def get_action_items():
    """Return the current list of action items."""
    try:
        with open("transcriptions/action_items.json", "r") as file:
            action_items = json.load(file)
        return jsonify(action_items)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"action_items": ""}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching action items: {str(e)}"}), 500


@app.route('/get-meeting-minutes', methods=['GET'])
def get_meeting_minutes():
    """Return the current meeting minutes summary."""
    try:
        with open("transcriptions/meeting_minutes.json", "r") as file:
            minutes = json.load(file)
        return jsonify(minutes)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"meeting_minutes": ""}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching meeting minutes: {str(e)}"}), 500


if __name__ == "__main__":
    socketio.run(app, port=8000, debug=True)
