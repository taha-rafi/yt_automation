import random
from datetime import datetime

# Organized quotes by categories
QUOTES = {
    'motivation': [
        "The best way to get started is to quit talking and begin doing.",
        "The pessimist sees difficulty in every opportunity. The optimist sees opportunity in every difficulty.",
        "Don't let yesterday take up too much of today.",
        "You learn more from failure than from success. Don't let it stop you. Failure builds character.",
        "It's not whether you get knocked down, it's whether you get up.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "The future belongs to those who believe in the beauty of their dreams.",
        "The only way to do great work is to love what you do.",
        "Your time is limited, don't waste it living someone else's life.",
        "Everything you've ever wanted is on the other side of fear."
    ],
    'success': [
        "Success usually comes to those who are too busy to be looking for it.",
        "If you really want to do something, you'll find a way. If you don't, you'll find an excuse.",
        "The only place where success comes before work is in the dictionary.",
        "Don't watch the clock; do what it does. Keep going.",
        "The secret of success is to do the common things uncommonly well."
    ],
    'mindset': [
        "Whether you think you can or you think you can't, you're right.",
        "The mind is everything. What you think you become.",
        "Your attitude determines your direction.",
        "Everything is possible when you believe in yourself.",
        "Change your thoughts and you change your world."
    ]
}

def get_random_quote(category=None):
    """
    Get a random motivational quote.
    Args:
        category (str, optional): Specific category to choose from ('motivation', 'success', 'mindset')
    Returns:
        tuple: (quote, category)
    """
    if category and category in QUOTES:
        quotes_list = QUOTES[category]
    else:
        # If no category specified or invalid category, choose from all categories
        category = random.choice(list(QUOTES.keys()))
        quotes_list = QUOTES[category]
    
    quote = random.choice(quotes_list)
    return quote, category

def generate_title_and_description(quote, category):
    """
    Generate YouTube Shorts title and description.
    """
    # Get current date for the description
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Create title with category and emoji
    emojis = {
        'motivation': '🔥',
        'success': '⭐',
        'mindset': '🧠'
    }
    
    title = f"{emojis.get(category, '✨')} {category.title()} Quote of the Day #Shorts"
    
    # Create description with hashtags
    description = f"{quote}\n\n📅 {current_date}\n\n"
    description += f"#motivation #{category} #inspirational #quotes #viral #trending #shorts"
    
    return title, description

if __name__ == "__main__":
    quote, category = get_random_quote()
    title, description = generate_title_and_description(quote, category)
    print(f"Quote: {quote}")
    print(f"Category: {category}")
    print(f"Title: {title}")
    print(f"Description: {description}")