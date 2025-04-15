from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
import requests
from scripts.utils import logger

class ApprovalSystem:
    def __init__(self, token):
        self.token = token
        self.pending_approvals = {}
        self.config_file = 'config.json'
        self.load_config()
        self.openrouter_api_key = self.config.get('openrouter_api_key', '')

    def load_config(self):
        """Load configuration including admin chat IDs"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'admin_chat_ids': [],
                'auto_approve_after': 30,
                'openrouter_api_key': ''
            }
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command"""
        await update.message.reply_text(
            "Welcome to YouTube Shorts Approval Bot!\n"
            "Use /register to register as an admin.\n"
            "Use /status to check pending approvals."
        )

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /register command"""
        chat_id = update.effective_chat.id
        if chat_id not in self.config['admin_chat_ids']:
            self.config['admin_chat_ids'].append(chat_id)
            self.save_config()
            await update.message.reply_text("You are now registered as an admin!")
        else:
            await update.message.reply_text("You are already registered as an admin.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command"""
        if not self.pending_approvals:
            await update.message.reply_text("No pending approvals.")
            return

        status_text = "Pending Approvals:\n\n"
        for video_id, info in self.pending_approvals.items():
            status_text += f"Video: {info['title']}\n"
            status_text += f"Category: {info['category']}\n"
            status_text += f"Created: {info['timestamp']}\n\n"

        await update.message.reply_text(status_text)

    def check_content(self, text):
        """Check content using OpenRouter's moderation capabilities"""
        try:
            if not self.openrouter_api_key:
                logger.error("OpenRouter API key not found in config")
                return False

            headers = {
                "HTTP-Referer": "https://youtube-shorts-generator.com",
                "X-Title": "YouTube Shorts Generator",
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "mistralai/mistral-7b-instruct:free",  # Using free Mistral model
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a content moderator. Your job is to check if content is safe and appropriate. Respond with only 'ACCEPT' or 'REJECT'."
                        },
                        {
                            "role": "user",
                            "content": f"Check if this content is safe and appropriate: {text}\nRespond with only ACCEPT or REJECT."
                        }
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.text}")
                return False

            data = response.json()
            result = data['choices'][0]['message']['content'].strip().upper()

            return result == "ACCEPT"

        except Exception as e:
            logger.error(f"Error in content moderation: {e}")
            return False

    async def request_approval(self, video_info):
        """Request approval for a video with content moderation"""
        # First check content with OpenRouter moderation
        content_to_check = f"{video_info['title']}\n{video_info['quote']}"
        moderation_passed = self.check_content(content_to_check)

        if not moderation_passed:
            print("Content rejected by automatic moderation")
            return False

        if not self.config['admin_chat_ids']:
            print("No admin chat IDs configured. Auto-approving moderated content...")
            return True

        video_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.pending_approvals[video_id] = {
            **video_info,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{video_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{video_id}")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"🎥 New Video Ready for Review\n\n"
            f"Title: {video_info['title']}\n"
            f"Category: {video_info['category']}\n"
            f"Quote: {video_info['quote']}\n\n"
            f"Video file: {video_info['video_path']}"
        )

        app = Application.builder().token(self.token).build()

        # Send approval request to all admins
        for chat_id in self.config['admin_chat_ids']:
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Failed to send approval request to {chat_id}: {e}")

        # Set up auto-approval timer
        if self.config['auto_approve_after'] > 0:
            await asyncio.sleep(self.config['auto_approve_after'] * 60)
            if video_id in self.pending_approvals:
                print(f"Auto-approving video {video_id} after timeout")
                return True

        return False

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle approval/rejection callbacks"""
        query = update.callback_query
        action, video_id = query.data.split('_')

        if video_id not in self.pending_approvals:
            await query.answer("This approval request has expired.")
            return

        video_info = self.pending_approvals[video_id]

        if action == "approve":
            del self.pending_approvals[video_id]
            await query.answer("Video approved!")
            await query.edit_message_text(
                f"✅ Video Approved!\n\n"
                f"Title: {video_info['title']}\n"
                f"Category: {video_info['category']}"
            )
            return True
        else:
            del self.pending_approvals[video_id]
            await query.answer("Video rejected!")
            await query.edit_message_text(
                f"❌ Video Rejected\n\n"
                f"Title: {video_info['title']}\n"
                f"Category: {video_info['category']}"
            )
            return False

    def run(self):
        """Start the Telegram bot"""
        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("register", self.register_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CallbackQueryHandler(self.handle_callback))

        print("Approval bot is running...")
        app.run_polling()

if __name__ == "__main__":
    # For testing, replace with your Telegram bot token
    approval_system = ApprovalSystem("YOUR_BOT_TOKEN_HERE")
    approval_system.run()