import os
import json
from pathlib import Path
import time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from scripts.utils import logger

class YouTubeUploader:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / 'config.json'
        self.credentials_path = Path(__file__).parent.parent / 'credentials.json'
        self.token_path = Path(__file__).parent.parent / 'token.json'
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def load_credentials(self):
        """Load or refresh YouTube API credentials"""
        try:
            if self.token_path.exists():
                credentials = Credentials.from_authorized_user_file(
                    str(self.token_path), ['https://www.googleapis.com/auth/youtube.upload']
                )
                if credentials and credentials.valid:
                    return credentials
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    return credentials

            # If no valid credentials, need to authenticate
            if not self.credentials_path.exists():
                logger.error("credentials.json not found. Please download it from Google Cloud Console.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), ['https://www.googleapis.com/auth/youtube.upload']
            )
            credentials = flow.run_local_server(port=0)

            # Save credentials
            with open(self.token_path, 'w') as token:
                token.write(credentials.to_json())

            return credentials

        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None

    def upload_video(self, video_file, title, description, privacy_status="public"):
        """Upload video to YouTube with retries"""
        credentials = self.load_credentials()
        if not credentials:
            return False

        youtube = build('youtube', 'v3', credentials=credentials)

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['shorts']
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Upload attempt {attempt + 1}/{self.max_retries}")
                
                # Insert video
                insert_request = youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=MediaFileUpload(
                        video_file, 
                        chunksize=-1, 
                        resumable=True
                    )
                )

                # Upload with progress tracking
                response = None
                while response is None:
                    status, response = insert_request.next_chunk()
                    if status:
                        logger.info(f"Uploaded {int(status.progress() * 100)}%")

                logger.info(f"Upload Complete! Video ID: {response['id']}")
                return True

            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:  # Retry on server errors
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.warning(f"Upload failed, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                logger.error(f"Upload failed: {e}")
                return False
                
            except Exception as e:
                logger.error(f"Unexpected error during upload: {e}")
                return False

        return False

def upload_to_youtube(video_file, title, description):
    """Main upload function"""
    uploader = YouTubeUploader()
    return uploader.upload_video(video_file, title, description)

if __name__ == "__main__":
    # Test video upload
    from scripts.utils import setup_logging
    logger = setup_logging()
    upload_to_youtube("output.mp4", "Test Video", "Test Description")