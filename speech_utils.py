import pyaudio
from google.cloud import speech

import os
if __name__ == "__main__":
    os.set_start_method("spawn")


def transcribe_streaming():
    """Stream and transcribe audio in real-time."""
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)

    print("Listening... Press Ctrl+C to stop.")

    def generator():
        while True:
            yield stream.read(1024)

    # Send audio chunks to Google Cloud and get responses
    requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in generator())
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    transcription = ""

    try:
        for response in responses:
            for result in response.results:
                transcript = result.alternatives[0].transcript
                transcription += transcript + " "

                # Save transcription to a file
                with open("transcriptions/live_transcription.txt", "a") as f:
                    f.write(transcript + "\n")

                # Print the transcription to the console
                print("Transcript:", transcript)
    except Exception as e:
        print(f"Error during streaming transcription: {e}")
