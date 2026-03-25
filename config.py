import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("8332597382:AAHPEtuQKJiWdpGqIUJNslvuxUim8xCP8M0", "8332597382:AAHPEtuQKJiWdpGqIUJNslvuxUim8xCP8M0")

# Настройки игры
DEFAULT_MAX_PLAYERS = 6
DEFAULT_SURVIVORS = 3
DISCUSSION_TIME = 90
VOTE_TIME = 45

# Пути
DATA_PATH = "data/cards.csv"
# ... (существующие) ...
DISCUSSION_TIME = 90   # секунд
VOTE_TIME = 45         # секунд