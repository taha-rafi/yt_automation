import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import json
from telegram import Update
from telegram.ext import ContextTypes
from scripts.approval_system import ApprovalSystem
from test_config import TEST_CONFIG

class TestApprovalSystem:
    @pytest.fixture
    def approval_system(self):
        return ApprovalSystem(TEST_CONFIG['telegram_token'])

    @pytest.fixture
    def test_output_dir(self, tmp_path):
        return tmp_path / 'test_output'

    @pytest.fixture(autouse=True)
    def setup_teardown(self, test_output_dir):
        test_output_dir.mkdir(exist_ok=True)
        yield
        if test_output_dir.exists():
            for file in test_output_dir.glob('*'):
                try:
                    file.unlink()
                except:
                    pass
            test_output_dir.rmdir()

    @pytest.mark.asyncio
    @patch('scripts.approval_system.OpenAI')
    @patch('telegram.ext.Application')
    async def test_request_approval_with_moderation(self, mock_telegram, mock_openai, approval_system, test_output_dir):
        # Mock OpenAI moderation response
        mock_moderation = MagicMock()
        mock_moderation.results = [MagicMock(flagged=False)]
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = mock_moderation
        mock_openai.return_value = mock_client

        # Mock Telegram bot
        mock_bot = AsyncMock()
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_telegram.builder.return_value.token.return_value.build.return_value = mock_app

        # Test video info
        video_info = {
            'title': 'Test Video',
            'category': 'motivation',
            'quote': 'Test quote',
            'video_path': str(test_output_dir / 'test.mp4')
        }

        # Create dummy video file
        with open(video_info['video_path'], 'wb') as f:
            f.write(b'dummy video')

        # Test approval request
        result = await approval_system.request_approval(video_info)
        assert result == True  # Should auto-approve in test mode
        mock_client.moderations.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('scripts.approval_system.OpenAI')
    @patch('telegram.ext.Application')
    async def test_request_approval_flagged_content(self, mock_telegram, mock_openai, approval_system, test_output_dir):
        # Mock OpenAI moderation response for flagged content
        mock_moderation = MagicMock()
        mock_moderation.results = [MagicMock(
            flagged=True,
            categories={'hate': True, 'violence': False}
        )]
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = mock_moderation
        mock_openai.return_value = mock_client

        # Test video info
        video_info = {
            'title': 'Test Video',
            'category': 'test',
            'quote': 'Problematic content',
            'video_path': str(test_output_dir / 'test.mp4')
        }

        # Create dummy video file
        with open(video_info['video_path'], 'wb') as f:
            f.write(b'dummy video')

        # Test approval request
        result = await approval_system.request_approval(video_info)
        assert result == False  # Should be rejected due to content moderation

    @pytest.mark.asyncio
    async def test_handle_callback(self, approval_system):
        # Mock callback query
        mock_query = MagicMock()
        mock_query.data = "approve_123"  # This should now be a string, not a coroutine
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()

        # Mock update object
        mock_update = MagicMock(spec=Update)
        mock_update.callback_query = mock_query

        # Add test video to pending approvals
        approval_system.pending_approvals["123"] = {
            'title': 'Test Video',
            'category': 'test',
            'video_path': 'test_path'
        }

        # Test approval handling
        result = await approval_system.handle_callback(mock_update, None)
        assert result == True
        assert "123" not in approval_system.pending_approvals
        mock_query.answer.assert_awaited_once()
        mock_query.edit_message_text.assert_awaited_once()