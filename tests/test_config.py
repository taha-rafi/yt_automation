import os
import sys
from pathlib import Path

# Add parent directory to path to import from scripts
sys.path.append(str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    'openrouter_api_key': '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',
    'telegram_token': 'test_token',
    'auto_approve_after': 1,  # 1 minute for testing
    'admin_chat_ids': [123456789],
    'youtube': {
        'upload_defaults': {
            'privacy_status': 'private',  # Use private for testing
            'made_for_kids': False,
            'tags': ["test", "automation"]
        }
    }
}