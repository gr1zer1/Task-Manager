import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://api:8001")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
EXCHANGE_NAME = "tasks"
QUEUE_NAME = "task_events"
ROUTING_KEY = "task.*"

DEBUG = os.getenv("DEBUG", "True") == "True"
