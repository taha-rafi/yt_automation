from transformers import pipeline, set_seed
import random
import os
from pathlib import Path

class AIScriptGenerator:
    def __init__(self):
        # Set cache directory in the project folder
        cache_dir = Path(__file__).parent.parent / 'model_cache'
        os.environ['TRANSFORMERS_CACHE'] = str(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)

        # Use a smaller model for faster generation
        print("Loading AI model (this may take a moment the first time)...")
        self.generator = pipeline(
            'text-generation',
            model='distilgpt2',
            device=-1  # Use CPU
        )
        set_seed(42)  # For reproducibility

        # Topics for variety
        self.topics = [
            "success", "motivation", "personal growth",
            "leadership", "persistence", "courage",
            "creativity", "wisdom", "happiness",
            "achievement", "mindset", "determination"
        ]

    def _clean_generated_text(self, text, prefix=""):
        """Clean up generated text"""
        # Remove the prefix/prompt if present
        text = text.replace(prefix, "").strip()

        # Clean up quotation marks
        if text.count('"') % 2 == 1:
            text = text.split('"')[1] if '"' in text else text

        # Ensure proper sentence ending
        if not text.endswith(('.', '!', '?')):
            # Find the last complete sentence
            last_sentence = text.split('.')
            if len(last_sentence) > 1:
                text = last_sentence[0] + '.'
            else:
                text += '.'

        return text.strip()

    def generate_quote(self):
        """Generate an inspirational quote using AI"""
        topic = random.choice(self.topics)
        prompt = f"Write an inspiring quote about {topic} in one sentence:"

        try:
            # Generate text with parameters tuned for quotes
            result = self.generator(
                prompt,
                max_length=50,
                num_return_sequences=1,
                temperature=0.7,
                top_k=50,
                do_sample=True,
                truncation=True
            )

            quote = self._clean_generated_text(result[0]['generated_text'], prompt)

            # Fallback to traditional quotes if generated text is too short
            if len(quote) < 20:
                from .generate_script import get_random_quote
                return get_random_quote()

            return quote, topic

        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to traditional quotes if AI fails
            from .generate_script import get_random_quote
            return get_random_quote()

    def generate_variation(self, seed_quote):
        """Generate a variation of an existing quote"""
        prompt = f"Rewrite this quote differently: '{seed_quote}'"

        try:
            result = self.generator(
                prompt,
                max_length=50,
                num_return_sequences=1,
                temperature=0.8,
                top_k=50,
                do_sample=True
            )

            variation = self._clean_generated_text(result[0]['generated_text'], prompt)

            # If variation is too similar or too short, return original
            if len(variation) < 20 or variation.lower() == seed_quote.lower():
                return seed_quote

            return variation

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