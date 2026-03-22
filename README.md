# Anime Admin Release

Это готовый фронтенд-пакет панели управления.

## Что внутри
- Next.js 14
- React 18
- Тёмный релизный интерфейс
- Разделы: dashboard, content, media, users, roles, security, integrations, analytics, settings
- Простое создание карточки с прямой загрузкой фото или видео

## Как запустить локально
1. Распакуй архив
2. Открой папку проекта
3. Выполни:

```bash
npm install
npm run dev
```

4. Открой в браузере:

```text
http://localhost:3000
```

## Как загрузить на VPS
1. Залей папку в GitHub или скопируй на сервер
2. На сервере установи Node.js 20+
3. Выполни:

```bash
npm install
npm run build
npm run start
```

## Что делать дальше
1. Подтверди внешний вид интерфейса
2. После этого подключаем реальный backend API
3. Затем собираем единый прод-репозиторий с frontend + backend + docker
