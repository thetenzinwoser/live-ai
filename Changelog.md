# Change Log

## v1.0 - 1/20/2023
- Initial working version with live transcription and GPT integration.
- Chatbot that allows users to ask questions about the transcript.
- Transcript is added to with every new speech-to-text result.


## v1.1 - 1/20/2023
- Deleted transcribe_test.py which was the first attempt at non-live transcription.
- Organized file structure, added gpt_utils.py, added speech_utils.py, added .gitignore, added requirements.txt

## v1.2 - 1/20/2023
- Added diarization to live transcription.
- Began setting up Flask front end.

## v1.3 - 1/23/2023
- Added Flask front end.
- Added non-diarized transcription saved to txt file.
- Added utilities around asynchronous transcription for personal use currently.
- Functional front end to enable synchronous transcription.

## v1.4 - 1/23/2023
- Added GPT prompting and UI polishing.