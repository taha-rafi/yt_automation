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
        self.credentials_path = Path('credentials.json')
        self.token_path = Path('token.json')
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.api_service_name = "youtube"
        self.api_version = "v3"

    def load_credentials(self):
        """Load or create credentials for YouTube API"""
        creds = None
        try:
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.scopes)
                    creds = flow.run_local_server(port=0)

                # Save the credentials
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

            return creds

        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return None

    def upload_video(self, video_path, title, description, privacy_status="public", max_retries=3, thumbnail_path=None, tags=None):
        """Upload a video to YouTube"""
        try:
            creds = self.load_credentials()
            if not creds:
                return False

            youtube = build(
                self.api_service_name,
                self.api_version,
                credentials=creds,
                static_discovery=False
            )

            media = MediaFileUpload(video_path, resumable=True)
            snippet = {
                "title": title,
                "description": description
            }
            if tags:
                snippet["tags"] = tags

            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": snippet,
                    "status": {
                        "privacyStatus": privacy_status
                    }
                },
                media_body=media
            )

            for attempt in range(max_retries):
                try:
                    logger.info(f"Upload attempt {attempt + 1}/{max_retries}")
                    response = request.execute()
                    logger.info(f"Video upload successful! Video ID: {response['id']}")
                    # Upload thumbnail if provided
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        try:
                            youtube.thumbnails().set(
                                videoId=response['id'],
                                media_body=MediaFileUpload(thumbnail_path)
                            ).execute()
                            logger.info("Thumbnail uploaded successfully!")
                        except Exception as thumb_e:
                            logger.warning(f"Thumbnail upload failed: {thumb_e}")
                    return True
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Unexpected error during upload: {str(e)}")
                        return False
                    logger.warning(f"Upload attempt {attempt + 1} failed: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error setting up video upload: {str(e)}")
            return False

def upload_to_youtube(video_file, title, description, thumbnail_path=None, tags=None):
    """Main upload function"""
    uploader = YouTubeUploader()
    return uploader.upload_video(video_file, title, description, thumbnail_path=thumbnail_path, tags=tags)

if __name__ == "__main__":
    # Test video upload
    from scripts.utils import setup_logging
    logger = setup_logging()
    upload_to_youtube("output.mp4", "Test Video", "Test Description")