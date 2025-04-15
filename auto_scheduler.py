import schedule
import time
import asyncio
import json
from pathlib import Path
from datetime import datetime
import os
from scripts.ai_generator import AIScriptGenerator
from scripts.text_to_speech import text_to_speech
from scripts.online_video_creator import VideoCreator
from scripts.upload_youtube import upload_to_youtube
from scripts.approval_system import ApprovalSystem

class AutomatedYouTubeShorts:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.load_config()
        self.ai_generator = AIScriptGenerator()
        self.approval_system = ApprovalSystem(self.config['telegram_token'])
        self.video_creator = VideoCreator()
        self.ensure_directories()
        self.failed_attempts = 0
        self.max_failed_attempts = 3

    def load_config(self):
        """Load configuration from config.json"""
        config_path = self.project_root / 'config.json'
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                'telegram_token': '',
                'openrouter_api_key': '',
                'auto_approve_after': 30
            }

    def ensure_directories(self):
        """Ensure all required directories exist"""
        for dir_name in ['output', 'assets', 'approved', 'rejected']:
            os.makedirs(self.project_root / dir_name, exist_ok=True)

    def generate_paths(self):
        """Generate unique paths for files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {
            'audio': self.project_root / 'output' / f"speech_{timestamp}.mp3",
            'video': self.project_root / 'output' / f"video_{timestamp}.mp4"
        }

    async def create_and_approve_video(self):
        """Create a video and get approval with improved error handling"""
        try:
            # Generate paths
            paths = self.generate_paths()

            # Generate AI quote
            quote, topic = self.ai_generator.generate_quote()
            if not quote:
                raise ValueError("Failed to generate quote")
            print(f"\nGenerated Quote ({topic}): {quote}")

            # Create title and description
            title = f"🎯 AI-Generated {topic.title()} Quote #Shorts"
            description = f"{quote}\n\n"
            description += f"🤖 AI-Generated Wisdom | {datetime.now().strftime('%B %d, %Y')}\n\n"
            hashtags = list(set([topic, "motivation", "inspirational", "quotes", "shorts"]))
            description += " ".join([f"#{tag}" for tag in hashtags])

            # Generate speech
            print("Converting to speech...")
            if not text_to_speech(quote, str(paths['audio'])):
                raise RuntimeError("Failed to generate speech")

            # Create video
            print("Creating video...")
            if not self.video_creator.create_video(quote, str(paths['audio']), str(paths['video'])):
                raise RuntimeError("Failed to create video")

            # Request approval
            print("Requesting approval...")
            video_info = {
                'title': title,
                'category': topic,
                'quote': quote,
                'video_path': str(paths['video'])
            }

            approved = await self.approval_system.request_approval(video_info)

            if approved:
                print("Video approved! Uploading to YouTube...")
                if upload_to_youtube(str(paths['video']), title, description):
                    print("Upload successful!")
                    final_path = self.project_root / 'approved' / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    os.rename(paths['video'], final_path)
                    self.failed_attempts = 0  # Reset counter on success
                else:
                    raise RuntimeError("Failed to upload to YouTube")
            else:
                print("Video rejected.")
                rejected_path = self.project_root / 'rejected' / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                os.rename(paths['video'], rejected_path)

            # Clean up audio file
            if os.path.exists(paths['audio']):
                os.remove(paths['audio'])

        except Exception as e:
            print(f"Error in video creation process: {e}")
            self.failed_attempts += 1
            if self.failed_attempts >= self.max_failed_attempts:
                print("Too many failed attempts. Pausing for 1 hour...")
                await asyncio.sleep(3600)  # 1 hour
                self.failed_attempts = 0
            raise

    async def run_test(self):
        """Run a single video creation test"""
        print("Running in test mode...")
        await self.create_and_approve_video()
        print("Test completed!")

    def schedule_videos(self, times):
        """Schedule video creation at specific times"""
        for time_str in times:
            schedule.every().day.at(time_str).do(
                lambda: asyncio.run(self.create_and_approve_video())
            )
        print(f"Scheduled video creation for: {', '.join(times)}")

    def run(self, test_mode=False):
        """Run the automated system"""
        if test_mode:
            print("Starting test mode...")
            asyncio.run(self.run_test())
            return

        print("Starting YouTube Shorts Automation System...")
        print("Press Ctrl+C to stop")

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\nShutting down gracefully...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='YouTube Shorts Automation')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()

    # Create automation system
    auto_system = AutomatedYouTubeShorts()

    if not args.test:
        # Schedule videos at specific times (24-hour format)
        posting_times = ["10:00", "15:00", "20:00"]  # Post 3 times a day
        auto_system.schedule_videos(posting_times)

    # Run the system
    auto_system.run(test_mode=args.test)