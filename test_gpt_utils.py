import unittest
from unittest.mock import patch, MagicMock
from gpt_utils import chunk_transcription, process_long_transcription, generate_meeting_minutes

class MockResponse:
    def __init__(self, content):
        self.choices = [MagicMock(message=MagicMock(content=content))]

class TestGPTUtils(unittest.TestCase):
    def setUp(self):
        # Sample test transcript with multiple topics
        self.test_transcript = """
        Alice: Good morning everyone. Let's discuss the Q1 results.
        Bob: Sales are up 15% from last quarter.
        Charlie: That's great! What about the new product launch?
        
        Alice: Moving on to the marketing budget.
        Bob: We need to increase it by 20%.
        Charlie: I agree, especially for digital campaigns.
        
        Alice: Finally, let's talk about hiring.
        Bob: We have 5 open positions.
        Charlie: Let's prioritize the senior developer role.
        """

    def test_chunk_transcription(self):
        """Test if the transcript is properly chunked"""
        chunks = chunk_transcription(self.test_transcript, chunk_size=200)
        
        # Verify chunks are created
        self.assertTrue(len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}")
        
        # Verify each chunk has content
        for i, chunk in enumerate(chunks):
            self.assertTrue(chunk.strip(), f"Chunk {i} is empty")
            self.assertTrue(len(chunk) <= 200, f"Chunk {i} exceeds max size")

    @patch('gpt_utils.client.chat.completions.create')
    def test_process_long_transcription(self, mock_chat):
        """Test the rolling summary process"""
        # First verify we have enough chunks
        chunks = chunk_transcription(self.test_transcript, chunk_size=200)
        self.assertTrue(len(chunks) >= 3, f"Test setup error: not enough chunks ({len(chunks)})")
        
        # Mock responses for each chunk
        responses = [
            MockResponse("Q1 results discussed: 15% sales increase"),
            MockResponse("Marketing budget: 20% increase proposed"),
            MockResponse("Hiring: 5 open positions, focus on senior dev")
        ]
        
        # Configure mock to return responses in sequence
        mock_chat.side_effect = responses
        
        result = process_long_transcription(self.test_transcript)
        
        # Print debug information
        print(f"\nNumber of chunks: {len(chunks)}")
        print(f"Mock call count: {mock_chat.call_count}")
        print(f"Expected responses: {len(responses)}")
        print(f"Result: {result}")
        
        # Verify the mock was called the expected number of times
        self.assertEqual(mock_chat.call_count, len(responses), 
                        f"Expected {len(responses)} calls, got {mock_chat.call_count}")
        
        # Verify all parts of the rolling summary are present
        for expected_text in ["Q1 results", "Marketing budget", "Hiring"]:
            self.assertIn(expected_text, result, 
                         f"Expected to find '{expected_text}' in result")

    @patch('gpt_utils.client.chat.completions.create')
    def test_generate_meeting_minutes(self, mock_chat):
        """Test meeting minutes generation"""
        expected_minutes = """
        ## Q1 Review Meeting
        
        1. Sales Performance
           * Q1 sales increased by 15%
        
        2. Marketing Updates
           * Budget increase of 20% proposed
           * Focus on digital campaigns
        
        3. Hiring Plans
           - [ ] Fill 5 open positions
           - [ ] Priority: Senior Developer role
        """
        
        mock_chat.return_value = MockResponse(expected_minutes)
        
        result = generate_meeting_minutes(self.test_transcript)
        
        # Verify the meeting minutes format and content
        self.assertIn("Q1 Review Meeting", result)
        self.assertIn("Sales Performance", result)
        self.assertIn("Marketing Updates", result)
        self.assertIn("Hiring Plans", result)

if __name__ == '__main__':
    unittest.main() 