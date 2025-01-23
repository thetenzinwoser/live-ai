import threading
from flask import Flask, render_template, jsonify, request
from speech_utils import transcribe_streaming  # Import your transcription logic

app = Flask(__name__)
is_listening = False  # Global flag to track listening state

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start-listening", methods=["POST"])
def start_listening():
    global is_listening

    if not is_listening:  # Prevent multiple threads
        is_listening = True
        threading.Thread(target=transcribe_streaming).start()
        return jsonify({"message": "Listening started!"})
    else:
        return jsonify({"message": "Already listening."})
    

@app.route("/stop-listening", methods=["POST"])
def stop_listening():
    global is_listening
    is_listening = False
    return jsonify({"message": "Listening stopped!"})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
