from flask import Flask, request, jsonify, render_template
from gpt_utils import get_gpt_response  # Function to interact with ChatGPT
import threading
from speech_utils import transcribe_streaming  # Import your transcription logic

app = Flask(__name__, template_folder='templates')  # Specify the templates folder
is_listening = False  # Global flag to track listening state


@app.route("/start-listening", methods=["POST"])
def start_listening():
    """Start listening for transcription."""
    global is_listening

    if not is_listening:  # Prevent multiple threads
        is_listening = True
        threading.Thread(target=transcribe_streaming).start()
        return jsonify({"message": "Listening started!"})
    else:
        return jsonify({"message": "Already listening."})


@app.route("/stop-listening", methods=["POST"])
def stop_listening():
    """Stop listening for transcription."""
    global is_listening
    is_listening = False
    return jsonify({"message": "Listening stopped!"})


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


if __name__ == "__main__":
    app.run(port=8000, debug=True)
