# Anime Platform Release v2

В архиве уже есть:
- рабочий FastAPI backend
- рабочий Next.js admin
- Telegram bot service
- docker-compose

## Что реально работает
- login
- refresh token
- /auth/me
- users list
- create/update user
- roles list
- permissions list
- content list
- create content with direct file upload
- archive content
- settings read/update
- bot settings storage
- forgot/reset password
- Telegram bot: /start /health /catalog

## Что нужно заполнить руками
### backend/.env
При необходимости поменяй owner и secret.

### frontend/.env
Если frontend и api на одном сервере через docker-compose, оставь как есть или укажи внешний URL.

### bot/.env
Обязательно укажи:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_BOT_USERNAME

## Запуск
```bash
docker-compose up -d --build
```

## URL
- Admin: http://localhost:3000
- API: http://localhost:8000

## Дефолтный вход
- username: owner
- password: ChangeThisOwnerPassword123!
