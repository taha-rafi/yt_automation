import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import ffmpeg
from scripts.qwen_ai import QwenAI
from test_config import TEST_CONFIG
from ollama_python import Client

class TestQwenAI(unittest.TestCase):
    def setUp(self):
        self.qwen = QwenAI(TEST_CONFIG['openrouter_api_key'])
        self.test_output_dir = Path(__file__).parent / 'test_output'
        self.test_output_dir.mkdir(exist_ok=True)
        # Ensure ffmpeg path is set
        os.environ['PATH'] = str(Path(__file__).parent.parent / 'bin' / 'ffmpeg') + os.pathsep + os.environ['PATH']

    def tearDown(self):
        # Clean up test files
        if self.test_output_dir.exists():
            for file in self.test_output_dir.glob('*'):
                try:
                    file.unlink()
                except:
                    pass
            self.test_output_dir.rmdir()

    @patch('openai.OpenAI')
    def test_generate_creative_quote(self, mock_openai):
        # Mock the OpenAI API response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Test quote"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Test quote generation
        quote = self.qwen.generate_creative_quote("test")
        self.assertEqual(quote, "Test quote")
        mock_client.chat.completions.create.assert_called_once()

    def test_create_gradient_background(self):
        # Test gradient background creation
        image = self.qwen._create_gradient_background()
        self.assertEqual(image.size, (self.qwen.width, self.qwen.height))
        self.assertEqual(image.mode, 'RGB')

    def test_add_text_to_image(self):
        # Test text overlay
        image = self.qwen._create_gradient_background()
        test_text = "Test quote text"
        result = self.qwen._add_text_to_image(image, test_text)
        self.assertEqual(result.size, (self.qwen.width, self.qwen.height))

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('tempfile.gettempdir')
    def test_generate_video(self, mock_tempfile, mock_output, mock_input, mock_probe):
        # Mock tempfile
        temp_video = str(self.test_output_dir / 'temp_video.mp4')
        mock_tempfile.return_value = str(self.test_output_dir)

        # Mock ffmpeg probe response
        mock_probe.return_value = {'format': {'duration': '10.0'}}

        # Create mock stream object that implements the required interface
        mock_stream = MagicMock()
        mock_stream.__class__.__name__ = 'FilterableStream'
        mock_input.return_value = mock_stream

        # Mock ffmpeg output and run
        mock_output.return_value = mock_stream
        mock_stream.overwrite_output.return_value.run.return_value = (None, None)

        # Create dummy temp video file
        with open(temp_video, 'wb') as f:
            f.write(b'dummy video')

        # Test full video generation
        test_text = "Test quote for video"
        audio_path = str(self.test_output_dir / "test_audio.mp3")
        video_path = str(self.test_output_dir / "test_video.mp4")

        # Create a dummy audio file
        with open(audio_path, 'wb') as f:
            f.write(b'dummy audio')

        result = self.qwen.generate_video(test_text, audio_path, video_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(video_path))
        mock_input.assert_called()
        mock_output.assert_called()

if __name__ == '__main__':
    unittest.main()