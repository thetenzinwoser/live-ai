import threading
from gpt_utils import analyze_with_gpt
from speech_utils import transcribe_streaming

def handle_user_queries():
    """Continuously listen for user queries and process them with GPT."""
    transcription_file = "transcriptions/live_transcription.txt"

    while True:
        query = input("\nType your query (or type 'exit' to stop querying): ")
        if query.lower() == "exit":
            print("Exiting query system.")
            break

        try:
            with open(transcription_file, "r") as f:
                transcription = f.read()
        except FileNotFoundError:
            print("Transcription file not found yet.")
            continue

        # Analyze the query with GPT
        feedback = analyze_with_gpt(transcription, query)
        print("\n--- GPT Feedback ---")
        print(feedback)
        print("--------------------")

if __name__ == "__main__":
    # Run transcription and user query handling in parallel
    try:
        transcription_thread = threading.Thread(target=transcribe_streaming)
        query_thread = threading.Thread(target=handle_user_queries)

        transcription_thread.start()
        query_thread.start()

        transcription_thread.join()
        query_thread.join()
    except KeyboardInterrupt:
        print("\nStopped.")
