import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL")
MAX_TOKENS = int(os.getenv("MAX_TOKENS"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
