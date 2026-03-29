# Stage 13 - Card Builder UX + Bulk Selection

В архиве:
- весь stage 12
- убраны быстрые кнопки с dashboard
- упрощённое единое окно карточки
- поле "Жанр" в карточке
- авто-генерация кода внутри карточки
- множественный выбор для удаления
- множественный выбор для открытия нескольких страниц редактирования
- улучшенный вывод жанра в lookup и в боте

Новая логика:
- жанр хранится без ломки текущей БД
- жанр кодируется внутри title.description служебной меткой и потом извлекается обратно

Что проверять:
- /admin
- /admin/card-builder
- /admin/titles
- /admin/seasons
- /admin/episodes
- /admin/assets
- /admin/codes
- /admin/lookup-test
- Telegram bot reply
