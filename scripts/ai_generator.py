import random
import os
import json
from pathlib import Path
from .qwen_ai import QwenAI

class AIScriptGenerator:
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.qwen = QwenAI(config['openrouter_api_key'])
        # Topics for variety
        self.topics = [
            "success", "motivation", "personal growth",
            "leadership", "persistence", "courage",
            "creativity", "wisdom", "happiness",
            "achievement", "mindset", "determination"
        ]

    def _clean_generated_text(self, text):
        """Clean up generated text"""
        # Remove any quotes
        text = text.strip().strip('"').strip("'").strip()

        # Ensure proper sentence ending
        if not text.endswith(('.', '!', '?')):
            text += '.'

        return text

    def generate_quote(self):
        """Generate an inspirational quote using Qwen AI"""
        topic = random.choice(self.topics)

        try:
            # Generate quote using Qwen AI
            quote = self.qwen.generate_creative_quote(topic)

            if quote:
                quote = self._clean_generated_text(quote)
                return quote, topic

            # Fallback to traditional quotes if AI fails
            from .generate_script import get_random_quote
            return get_random_quote()

        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to traditional quotes if AI fails
            from .generate_script import get_random_quote
            return get_random_quote()

    def generate_variation(self, seed_quote):
        """Generate a variation of an existing quote using Qwen AI"""
        try:
            # We can use the same creative quote generation with the original quote as context
            variation = self.qwen.generate_creative_quote(f"Create a variation of this quote: {seed_quote}")

            if variation:
                variation = self._clean_generated_text(variation)
                # If variation is too similar or too short, return original
                if len(variation) < 20 or variation.lower() == seed_quote.lower():
                    return seed_quote
                return variation

            return seed_quote

        except Exception as e:
            print(f"Variation generation failed: {e}")
            return seed_quote

if __name__ == "__main__":
    # Test the AI generator
    generator = AIScriptGenerator()
    quote, topic = generator.generate_quote()
    print(f"Original Quote ({topic}): {quote}")
    variation = generator.generate_variation(quote)
    print(f"Variation: {variation}")