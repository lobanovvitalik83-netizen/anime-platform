# Anime Platform

Платформа управления Telegram + VK ботами, контентом, кодами и аналитикой.

## Стек
- FastAPI
- PostgreSQL
- Redis
- Docker
- SQLAlchemy

## Что уже есть
- запуск API через Docker
- подключение PostgreSQL / Redis
- модели users / roles / permissions
- сидирование permissions
- автоматическое создание первого owner
- базовые API для пользователей, ролей и permissions

## Запуск
1. Скопировать `.env.example` в `.env`
2. Запустить:
   docker-compose up -d --build

## Полезные URL
- API root: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
