# Anime Platform Release

В этом архиве:
- backend FastAPI с реальными endpoint-ами для auth, users, roles, permissions, settings
- frontend Next.js admin с живыми данными из backend
- docker-compose для запуска всей системы

## Реально работает
- вход
- refresh token
- current user
- список пользователей
- создание пользователя
- список ролей
- список permissions
- чтение и обновление settings
- forgot/reset password

## Запуск
1. Скопируй `.env.example` в `.env` в папках `backend` и `frontend`.
2. Подними:
```bash
docker-compose up -d --build
```

## Дефолтный вход
- username: owner
- password: ChangeThisOwnerPassword123!
