import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
EXCHANGE_NAME = "tasks"
QUEUE_NAME = "task_events"
ROUTING_KEY = "task.*"

DEBUG = os.getenv("DEBUG", "True") == "True"
