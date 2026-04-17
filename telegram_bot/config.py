import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8002")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

DEBUG = os.getenv("DEBUG", "True") == "True"
