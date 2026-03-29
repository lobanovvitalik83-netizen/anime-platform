# Stage 9 - Bot Card Pipeline

В архиве:
- весь stage 8
- улучшенный public lookup payload
- улучшенный выбор primary asset
- более понятная карточка для Telegram
- более безопасная отправка image / poster / video
- fallback на текстовую карточку, если медиа не отправилось
- нормализация caption под Telegram

Что проверять:
- /admin/assets
- /admin/lookup-test
- Telegram: /start
- Telegram: валидный код
- Telegram: код с image
- Telegram: код с video
- Telegram: код без ассета
