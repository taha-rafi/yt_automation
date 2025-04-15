import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
from scripts.text_to_speech import text_to_speech

class TestTextToSpeech(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = Path(__file__).parent / 'test_output'
        self.test_output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up test files
        for file in self.test_output_dir.glob('*'):
            file.unlink()
        self.test_output_dir.rmdir()

    @patch('gtts.gTTS')
    def test_text_to_speech_success(self, mock_gtts):
        # Mock gTTS
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance

        # Test TTS
        output_file = str(self.test_output_dir / 'test_speech.mp3')
        result = text_to_speech("Test speech text", output_file)
        
        self.assertTrue(result)
        mock_gtts.assert_called_once_with(text="Test speech text", lang='en')
        mock_tts_instance.save.assert_called_once_with(output_file)

    @patch('gtts.gTTS')
    def test_text_to_speech_api_error(self, mock_gtts):
        # Mock gTTS error
        mock_gtts.side_effect = Exception("gTTS Error")

        # Test error handling
        output_file = str(self.test_output_dir / 'test_speech.mp3')
        result = text_to_speech("Test speech text", output_file)
        
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_file))

if __name__ == '__main__':
    unittest.main()