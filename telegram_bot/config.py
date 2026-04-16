import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8000")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

# Service credentials для получения JWT
SERVICE_EMAIL = os.getenv("SERVICE_EMAIL", "bot@service.com")
SERVICE_PASSWORD = os.getenv("SERVICE_PASSWORD")

DEBUG = os.getenv("DEBUG", "True") == "True"
