# Anime Platform

Платформа управления Telegram + VK ботами, контентом, кодами и аналитикой.

## Стек
- FastAPI
- PostgreSQL
- Redis
- Docker

## Запуск
1. Скопировать `.env.example` в `.env`
2. Запустить:
   docker-compose up -d --build

## Сервисы
- API: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379
