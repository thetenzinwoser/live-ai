import pyaudio
from google.cloud import speech
from itertools import groupby

import os
if __name__ == "__main__":
    os.set_start_method("spawn")


import pyaudio
from google.cloud import speech

def transcribe_streaming():
    """Stream and transcribe audio in real-time with speaker diarization."""
    client = speech.SpeechClient()

    # Configure the audio stream with speaker diarization enabled
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        diarization_config=speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=2,
            max_speaker_count=2
        )
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # Set up microphone input
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

    processed_segments = set()  # To track and avoid repeated segments

    try:
        for response in responses:
            for result in response.results:
                if result.is_final:
                    words = result.alternatives[0].words
                    confidence = result.alternatives[0].confidence

                    # Initialize variables for grouping
                    grouped_transcription = []
                    current_speaker = None
                    current_phrase = []

                    for word in words:
                        # Check if the speaker changes
                        if current_speaker is None:
                            current_speaker = word.speaker_tag  # Initialize speaker
                        elif word.speaker_tag != current_speaker:
                            # Finalize the current speaker's phrase
                            if current_phrase:
                                phrase = " ".join(current_phrase)
                                segment = f"Speaker {current_speaker}: {phrase} (Confidence: {confidence:.2f})"
                                if segment not in processed_segments:
                                    grouped_transcription.append(segment)
                                    processed_segments.add(segment)
                            current_phrase = []  # Reset for the new speaker
                            current_speaker = word.speaker_tag  # Update speaker

                        # Append the current word
                        current_phrase.append(word.word)

                        # Finalize the phrase if punctuation is present
                        if word.word.endswith((".", "!", "?")):
                            phrase = " ".join(current_phrase)
                            segment = f"Speaker {current_speaker}: {phrase} (Confidence: {confidence:.2f})"
                            if segment not in processed_segments:
                                grouped_transcription.append(segment)
                                processed_segments.add(segment)
                            current_phrase = []  # Reset for the next sentence

                    # Finalize the last speaker's phrase
                    if current_phrase:
                        phrase = " ".join(current_phrase)
                        segment = f"Speaker {current_speaker}: {phrase} (Confidence: {confidence:.2f})"
                        if segment not in processed_segments:
                            grouped_transcription.append(segment)
                            processed_segments.add(segment)

                    # Save the grouped transcription to a file
                    with open("transcriptions/live_transcription.txt", "a") as f:
                        f.write("\n".join(grouped_transcription) + "\n")

                    # Print the grouped transcription to the console
                    print("\n".join(grouped_transcription))




    except Exception as e:
        print(f"Error during streaming transcription: {e}")



