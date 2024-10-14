import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')  # Токен Telegram бота
SQL_ALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:352142@localhost/postgres')
