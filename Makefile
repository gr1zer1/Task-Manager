.PHONY: help install dev docker-up docker-down docker-logs clean

help:
	@echo "📋 Task Manager - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies for all Python services"
	@echo "  make dev           - Run services in development mode"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     - Start all services with Docker Compose"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Remove .venv directories and cache files"

install:
	@echo "📦 Installing dependencies..."
	cd telegram_bot && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd event_consumer && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

dev:
	@echo "🚀 Starting services in development mode..."
	@echo "Starting RabbitMQ and PostgreSQL with Docker..."
	docker-compose up rabbitmq postgres -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Starting Telegram Bot..."
	cd telegram_bot && . .venv/bin/activate && python main.py &
	@echo "Starting Event Consumer..."
	cd event_consumer && . .venv/bin/activate && python main.py &
	@echo "✅ Services started"

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started"
	@echo "📊 RabbitMQ Management: http://localhost:15672 (guest/guest)"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped"

docker-logs:
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"
