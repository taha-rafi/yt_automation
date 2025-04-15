import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from scripts.upload_youtube import YouTubeUploader
from google.oauth2.credentials import Credentials

class TestYouTubeUploader(unittest.TestCase):
    def setUp(self):
        self.uploader = YouTubeUploader()
        self.test_dir = Path(__file__).parent / 'test_files'
        self.test_dir.mkdir(exist_ok=True)
        self.credentials_path = self.test_dir / 'test_credentials.json'
        self.token_path = self.test_dir / 'test_token.json'
        self.test_video = self.test_dir / 'test_video.mp4'

        # Create dummy test video file
        with open(self.test_video, 'wb') as f:
            f.write(b'dummy video content')

    def tearDown(self):
        # Clean up test files
        if self.test_video.exists():
            self.test_video.unlink()
        self.test_dir.rmdir()

    def test_load_credentials_existing(self):
        # Mock credentials
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.universe_domain = 'googleapis.com'

        # Override credentials path
        self.uploader.credentials_path = self.credentials_path
        self.uploader.token_path = self.token_path

        with patch('pathlib.Path.exists', return_value=True), \
             patch('google.oauth2.credentials.Credentials.from_authorized_user_file', return_value=mock_creds):
            creds = self.uploader.load_credentials()
            self.assertIsNotNone(creds)
            self.assertTrue(creds.valid)

    def test_load_credentials_new(self):
        # Mock credentials
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.universe_domain = 'googleapis.com'

        # Mock OAuth flow
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds

        # Override credentials path
        self.uploader.credentials_path = self.credentials_path
        self.uploader.token_path = self.token_path

        with patch('pathlib.Path.exists', return_value=False), \
             patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file', return_value=mock_flow), \
             patch('builtins.open', mock_open()):
            creds = self.uploader.load_credentials()
            self.assertIsNotNone(creds)
            self.assertTrue(creds.valid)

    def test_upload_video(self):
        # Mock credentials
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.universe_domain = 'googleapis.com'
        self.uploader.load_credentials = MagicMock(return_value=mock_creds)

        # Mock YouTube API client
        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.execute.return_value = {'id': 'test_video_id'}
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch('googleapiclient.discovery.build', return_value=mock_youtube):
            result = self.uploader.upload_video(
                str(self.test_video),
                "Test Title",
                "Test Description"
            )
            self.assertTrue(result)

    def test_upload_video_failure(self):
        # Mock credentials
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.universe_domain = 'googleapis.com'
        self.uploader.load_credentials = MagicMock(return_value=mock_creds)

        # Mock YouTube API client with error
        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.execute.side_effect = Exception("Upload failed")
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch('googleapiclient.discovery.build', return_value=mock_youtube):
            result = self.uploader.upload_video(
                str(self.test_video),
                "Test Title",
                "Test Description"
            )
            self.assertFalse(result)

    def test_upload_video_with_retries(self):
        # Mock credentials
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.universe_domain = 'googleapis.com'
        self.uploader.load_credentials = MagicMock(return_value=mock_creds)

        # Mock YouTube API client
        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.execute.side_effect = [
            Exception("Server Error"),  # First failure
            Exception("Server Error"),  # Second failure
            {'id': 'test_video_id'}  # Success
        ]
        mock_youtube.videos.return_value.insert.return_value = mock_request

        with patch('googleapiclient.discovery.build', return_value=mock_youtube):
            result = self.uploader.upload_video(
                str(self.test_video),
                "Test Title",
                "Test Description"
            )
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()