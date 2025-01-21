from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start-transcription", methods=["POST"])
def start_transcription():
    # Placeholder response for now
    return jsonify({"message": "Transcription started!"})

if __name__ == "__main__":
    app.run(debug=True, port=8000)
