from google.cloud import speech

def transcribe_audio():
    # Initialize the Speech-to-Text client
    client = speech.SpeechClient()

    # Path to the audio file
    audio_file = "audio1934314686.wav"

    # Read the audio file into memory
    with open(audio_file, "rb") as f:
        audio_content = f.read()

    # Configure the request
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    # Send the request to Google Cloud
    response = client.recognize(config=config, audio=audio)

    # Print the transcription
    for result in response.results:
        print("Transcript:", result.alternatives[0].transcript)

if __name__ == "__main__":
    transcribe_audio()
