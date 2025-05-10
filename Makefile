# Makefile для проекта Telegram-бота

PROJECT_NAME=telegram-bot

build:
	@echo "🚀 Сборка Docker-контейнера..."
	sudo docker-compose build

up:
	@echo "⬆️  Запуск контейнера в фоне..."
	sudo docker-compose up -d

down:
	@echo "🛑 Остановка и удаление контейнеров..."
	sudo docker-compose down

restart:
	@echo "🔄 Перезапуск контейнера..."
	sudo docker-compose restart

logs:
	@echo "📋 Просмотр логов..."
	sudo docker-compose logs -f

clean:
	@echo "🧹 Полная очистка: контейнеры, образы, тома..."
	sudo docker-compose down --volumes --remove-orphans
	sudo docker image prune -a -f
	sudo docker builder prune -a -f

shell:
	@echo "🐚 Вход в контейнер..."
	sudo docker exec -it $(PROJECT_NAME) bash
