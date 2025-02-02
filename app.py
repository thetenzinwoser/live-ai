from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO
from flask_session import Session
import speech_utils  # Import the whole module
from events import socketio
import json
import threading
from gpt_utils import get_gpt_response
from speech_utils import get_full_transcription
import os

app = Flask(__name__, template_folder='templates')  # Specify the templates folder
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # Change in production
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio.init_app(app)
is_listening = False  # Global flag to track listening state

# Hardcoded users (replace with database in production)
USERS = {
    "user1": "user1",
    "user2": "user2"
}

# Base directory for user transcriptions
BASE_DIR = os.path.join("transcriptions", "users")

def get_user_dir():
    """Get the current user's transcription directory."""
    if 'user' not in session:
        return None
    user_dir = os.path.join(BASE_DIR, session['user'])
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def user_required(f):
    """Decorator to require user authentication."""
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    wrapped.__name__ = f.__name__
    return wrapped

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return jsonify({"message": "Login successful"})
        return jsonify({"error": "Invalid credentials"}), 401
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        user_dir = get_user_dir()
        if user_dir:
            # Stop any active transcription
            speech_utils.stop_transcription(user_dir)
        session.pop('user', None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route("/start-listening", methods=["POST"])
@user_required
def start_listening():
    """Start listening for transcription and clear previous session data."""
    user_dir = get_user_dir()
    if not user_dir:
        return jsonify({"error": "Unauthorized"}), 401

    # Clear user's transcription files
    for filename in ["live_transcription.txt", "questions_answers.json", 
                    "action_items.json", "meeting_minutes.json"]:
        filepath = os.path.join(user_dir, filename)
        with open(filepath, "w") as f:
            if filename.endswith('.json'):
                json.dump([] if filename == "questions_answers.json" else {}, f)
            else:
                f.write("")

    # Start transcription thread for user
    threading.Thread(target=speech_utils.transcribe_streaming, 
                    args=(user_dir,)).start()

    return jsonify({"message": "Listening started, previous session cleared!"})


@app.route("/stop-listening", methods=["POST"])
def stop_listening():
    """Stop listening for transcription."""
    global is_listening
    if is_listening:
        is_listening = False
        speech_utils.stop_transcription()  # Add this line to stop the transcription
        return jsonify({"message": "Listening stopped. Data retained until next session starts."})
    return jsonify({"message": "Already stopped."})


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


@app.route('/get-transcript')
@user_required
def get_transcript():
    try:
        user_dir = get_user_dir()
        if not user_dir:
            return jsonify({'error': 'Unauthorized'}), 401

        filepath = os.path.join(user_dir, 'live_transcription.txt')
        with open(filepath, 'r') as file:
            lines = file.readlines()
            # Return lines in reverse chronological order
            return jsonify({'lines': lines[::-1]})
    except FileNotFoundError:
        return jsonify({'lines': []})
    except Exception as e:
        print(f"Error reading transcript: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-questions')
@user_required
def get_questions():
    try:
        user_dir = get_user_dir()
        if not user_dir:
            return jsonify({'error': 'Unauthorized'}), 401

        filepath = os.path.join(user_dir, 'questions_answers.json')
        with open(filepath, 'r') as file:
            qa_data = json.load(file)
            return jsonify({'questions': qa_data})
    except FileNotFoundError:
        return jsonify({'questions': []})
    except Exception as e:
        print(f"Error reading questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-action-items')
@user_required
def get_action_items():
    try:
        user_dir = get_user_dir()
        if not user_dir:
            return jsonify({'error': 'Unauthorized'}), 401

        filepath = os.path.join(user_dir, 'action_items.json')
        with open(filepath, 'r') as file:
            action_items = json.load(file)
        return jsonify(action_items)
    except FileNotFoundError:
        return jsonify({"action_items": ""})
    except Exception as e:
        return jsonify({"error": f"Error fetching action items: {str(e)}"}), 500

@app.route('/get-meeting-minutes')
@user_required
def get_meeting_minutes():
    try:
        user_dir = get_user_dir()
        if not user_dir:
            return jsonify({'error': 'Unauthorized'}), 401

        filepath = os.path.join(user_dir, 'meeting_minutes.json')
        with open(filepath, 'r') as file:
            minutes = json.load(file)
        return jsonify(minutes)
    except FileNotFoundError:
        return jsonify({"meeting_minutes": ""})
    except Exception as e:
        return jsonify({"error": f"Error fetching meeting minutes: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
@user_required
def chat():
    try:
        user_dir = get_user_dir()
        if not user_dir:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        
        # Get current transcription context from user's directory
        filepath = os.path.join(user_dir, 'live_transcription.txt')
        with open(filepath, 'r') as file:
            context = file.read()
        
        # Get response from GPT
        response = get_gpt_response(user_message, context)
        
        return jsonify({
            'response': response
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': 'Internal server error',
            'response': 'Sorry, there was an error processing your message.'
        }), 500


if __name__ == "__main__":
    socketio.run(app, port=8000, debug=True)
