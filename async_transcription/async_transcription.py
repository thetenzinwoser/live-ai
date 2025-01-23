import os
import ffmpeg
from google.cloud import speech
from google.cloud import storage

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """
    Uploads a file to Google Cloud Storage.

    :param bucket_name: Name of the GCS bucket.
    :param source_file_name: Path to the file to upload.
    :param destination_blob_name: Desired name of the file in the bucket.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")


def convert_to_flac(input_audio, output_flac):
    """
    Converts an audio file (mp4, m4a, or wav) to FLAC format using ffmpeg.
    """
    temp_wav = "temp.wav"  # Temporary WAV file

    try:
        # Convert m4a or mp4 to wav if needed
        if input_audio.endswith(".mp4") or input_audio.endswith(".m4a"):
            ffmpeg.input(input_audio).output(temp_wav).run(overwrite_output=True)
            print(f"Converted {input_audio} to {temp_wav}")
        else:
            temp_wav = input_audio  # Assume input is already a valid WAV file

        # Convert wav to flac
        ffmpeg.input(temp_wav).output(output_flac).run(overwrite_output=True)
        print(f"Converted {temp_wav} to {output_flac}")
    except Exception as e:
        print(f"Error converting file: {e}")
    finally:
        # Clean up temporary WAV file if it was created
        if (input_audio.endswith(".mp4") or input_audio.endswith(".m4a")) and os.path.exists(temp_wav):
            os.remove(temp_wav)

def transcribe_audio(input_audio, output_txt):
    """
    Transcribes a large audio file using Google's long-running recognize and saves the result.

    :param input_audio: Path to the input audio file.
    :param output_txt: Path to save the transcription result.
    """
    # Set up Google Speech client
    client = speech.SpeechClient()

    # Convert audio to FLAC
    flac_file = "temp.flac"
    convert_to_flac(input_audio, flac_file)

    # Upload the FLAC file to GCS
    bucket_name = "live-ai-bucket-1"  # Replace with your bucket name
    gcs_blob_name = "temp.flac"
    upload_to_gcs(bucket_name, flac_file, gcs_blob_name)

    # Set GCS URI for the uploaded file
    gcs_uri = f"gs://{bucket_name}/{gcs_blob_name}"

    # Configure recognition settings
    audio_config = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        language_code="en-US",
        audio_channel_count=2  # Set to match the channel count in your FLAC file
    )


    # Perform long-running recognition
    operation = client.long_running_recognize(config=config, audio=audio_config)
    print("Waiting for operation to complete...")
    response = operation.result(timeout=1800)  # Adjust timeout as needed

    # Process and save results
    with open(output_txt, "w") as txt_file:
        for result in response.results:
            txt_file.write(result.alternatives[0].transcript + "\n")
    print(f"Transcription saved to {output_txt}")

    # Clean up temporary files
    os.remove(flac_file)


if __name__ == "__main__":
    input_audio = input("Enter the path to your audio file (mp4, m4a, wav): ")
    output_txt = input("Enter the path to save the transcription (e.g., 'output.txt'): ")
    transcribe_audio(input_audio, output_txt)
