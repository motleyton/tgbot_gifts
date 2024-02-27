import logging
import os
from dotenv import load_dotenv

from tools import GoogleSearchTool
from openai_helper import OpenAIClient
from telegram_bot import GiftBot


def main():
    # Read .env file
    load_dotenv()
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Check if the required environment variables are set
    required_values = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    if missing_values := [
        value for value in required_values if os.environ.get(value) is None
    ]:
        logging.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)
    # Setup configurations
    model = os.environ.get('OPENAI_MODEL')
    openai_config = {
        'openai_api_key': os.environ['OPENAI_API_KEY'],
        'temperature': float(os.environ.get('TEMPERATURE')),
        'model': model,

    }
    telegram_config = {
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
        'bot_language': os.environ.get('BOT_LANGUAGE', 'en'),
    }
    google_search_config = {
        'google_api_key': os.environ['GOOGLE_API_KEY'],
        'google_cse_id': os.environ['GOOGLE_CSE_ID'],
    }

    # Setup and run ChatGPT and Telegram bot
    openai = OpenAIClient(config=openai_config)
    google_search_tool = GoogleSearchTool(config=google_search_config)
    telegram_bot = GiftBot(config=telegram_config, openai=openai, google_search=google_search_tool)

    telegram_bot.run()


if __name__ == '__main__':
    main()