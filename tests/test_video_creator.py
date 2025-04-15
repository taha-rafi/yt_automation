import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import ffmpeg
from scripts.online_video_creator import VideoCreator
from scripts.qwen_ai import QwenAI
from test_config import TEST_CONFIG

class TestVideoCreator(unittest.TestCase):
    def setUp(self):
        self.video_creator = VideoCreator()
        self.test_output_dir = Path(__file__).parent / 'test_output'
        self.test_output_dir.mkdir(exist_ok=True)

        # Create test audio file
        self.test_audio = self.test_output_dir / 'test_audio.mp3'
        with open(self.test_audio, 'wb') as f:
            f.write(b'dummy audio')

        # Set ffmpeg path
        os.environ['PATH'] = str(Path(__file__).parent.parent / 'bin' / 'ffmpeg') + os.pathsep + os.environ['PATH']

    def tearDown(self):
        if self.test_output_dir.exists():
            for file in self.test_output_dir.glob('*'):
                try:
                    file.unlink()
                except:
                    pass
            self.test_output_dir.rmdir()

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('tempfile.gettempdir')
    def test_create_video_success(self, mock_tempfile, mock_output, mock_input, mock_probe):
        # Mock tempfile path
        temp_video = str(self.test_output_dir / 'temp_video.mp4')
        mock_tempfile.return_value = str(self.test_output_dir)

        # Mock ffmpeg
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

        # Test video creation
        output_file = str(self.test_output_dir / 'test_video.mp4')
        with patch('scripts.online_video_creator.QwenAI') as mock_qwen_class:
            mock_instance = mock_qwen_class.return_value
            mock_instance.generate_video.side_effect = lambda text, audio, output, progress_callback=None: True

            result = self.video_creator.create_video(
                "Test quote",
                str(self.test_audio),
                output_file
            )

            self.assertTrue(result)
            mock_instance.generate_video.assert_called_once()

    @patch('scripts.online_video_creator.QwenAI')
    def test_create_video_failure(self, mock_qwen_ai):
        # Mock QwenAI failure
        mock_instance = mock_qwen_ai.return_value
        mock_instance.generate_video.return_value = False

        # Test error handling
        output_file = str(self.test_output_dir / 'test_video.mp4')
        result = self.video_creator.create_video(
            "Test quote",
            str(self.test_audio),
            output_file
        )

        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_file))

    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('tempfile.gettempdir')
    def test_create_video_with_progress(self, mock_tempfile, mock_output, mock_input, mock_probe):
        # Mock tempfile path
        temp_video = str(self.test_output_dir / 'temp_video.mp4')
        mock_tempfile.return_value = str(self.test_output_dir)

        # Mock ffmpeg
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

        # Test video creation with progress tracking
        output_file = str(self.test_output_dir / 'test_video.mp4')
        with patch('scripts.online_video_creator.QwenAI') as mock_qwen_class:
            mock_instance = mock_qwen_class.return_value

            def progress_side_effect(*args, **kwargs):
                progress_callback = kwargs.get('progress_callback')
                if progress_callback:
                    for progress in [0.2, 0.5, 0.8, 1.0]:
                        progress_callback(progress)
                return True

            mock_instance.generate_video.side_effect = progress_side_effect

            result = self.video_creator.create_video(
                "Test quote",
                str(self.test_audio),
                output_file
            )

            self.assertTrue(result)
            mock_instance.generate_video.assert_called_once()

if __name__ == '__main__':
    unittest.main()