import schedule
import time
import asyncio
from pathlib import Path
from datetime import datetime
import os
from scripts.ai_generator import AIScriptGenerator
from scripts.text_to_speech import text_to_speech
from scripts.create_video import create_video
from scripts.upload_youtube import upload_to_youtube
from scripts.approval_system import ApprovalSystem

class AutomatedYouTubeShorts:
    def __init__(self, telegram_token, test_mode=False):
        self.project_root = Path(__file__).parent.absolute()
        self.ai_generator = AIScriptGenerator()
        self.approval_system = ApprovalSystem(telegram_token)
        self.test_mode = test_mode
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        os.makedirs('output', exist_ok=True)
        os.makedirs('assets', exist_ok=True)
        os.makedirs('approved', exist_ok=True)
        os.makedirs('rejected', exist_ok=True)
    
    def generate_paths(self):
        """Generate unique paths for files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {
            'audio': f"output/speech_{timestamp}.mp3",
            'video': f"output/video_{timestamp}.mp4"
        }
    
    async def create_and_approve_video(self):
        """Create a video and get approval"""
        try:
            # Generate paths
            paths = self.generate_paths()
            
            # Generate AI quote
            quote, topic = self.ai_generator.generate_quote()
            print(f"\nGenerated Quote ({topic}): {quote}")
            
            # Create title and description
            title = f"🎯 AI-Generated {topic.title()} Quote #Shorts"
            description = f"{quote}\n\n"
            description += f"🤖 AI-Generated Wisdom | {datetime.now().strftime('%B %d, %Y')}\n\n"
            # Generate unique hashtags
            hashtags = list(set([topic, "motivation", "inspirational", "quotes", "shorts"]))
            description += " ".join([f"#{tag}" for tag in hashtags])
            
            # Generate speech
            print("Converting to speech...")
            text_to_speech(quote, paths['audio'])
            
            # Create video
            print("Creating video...")
            background_image = str(self.project_root / "assets" / "background.jpg")
            create_video(background_image, paths['audio'], paths['video'])
            
            # Request approval
            print("Requesting approval...")
            video_info = {
                'title': title,
                'category': topic,
                'quote': quote,
                'video_path': paths['video']
            }
            
            approved = await self.approval_system.request_approval(video_info)
            
            if approved:
                print("Video approved! Uploading to YouTube...")
                upload_to_youtube(paths['video'], title, description)
                # Move to approved folder
                os.rename(paths['video'], f"approved/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            else:
                print("Video rejected.")
                # Move to rejected folder
                os.rename(paths['video'], f"rejected/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            
            # Clean up audio file
            os.remove(paths['audio'])
            
        except Exception as e:
            print(f"Error in video creation process: {e}")
    
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
    
    def run(self):
        """Run the automated system"""
        if self.test_mode:
            print("Starting test mode...")
            asyncio.run(self.run_test())
            return

        print("Starting YouTube Shorts Automation System...")
        print("Press Ctrl+C to stop")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='YouTube Shorts Automation')
    parser.add_argument('--token', help='Telegram Bot Token', required=True)
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()
    
    # Create automation system
    auto_system = AutomatedYouTubeShorts(args.token, test_mode=args.test)
    
    if not args.test:
        # Schedule videos at specific times (24-hour format)
        posting_times = ["10:00", "15:00", "20:00"]  # Post 3 times a day
        auto_system.schedule_videos(posting_times)
    
    # Run the system
    auto_system.run()