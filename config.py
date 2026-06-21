import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN', '').strip()
CLIENT_ID = os.getenv('CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('CLIENT_SECRET', '').strip()
REDIRECT_URI = os.getenv('REDIRECT_URI', '').strip()
PORT = int(os.getenv('PORT', 3000))
GUILD_ID = os.getenv('GUILD_ID', '').strip()
