# Stage 12 - Card Builder + Media Upload

В архиве:
- весь stage 11
- единое окно создания карточки контента
- автоматическая генерация кода внутри карточки
- загрузка изображения/видео в Telegram и сохранение telegram_file_id
- fallback на external_url
- результат создания карточки прямо на странице

Новые ENV:
- TELEGRAM_MEDIA_UPLOAD_CHAT_ID
- ALLOWED_IMAGE_MIME
- ALLOWED_VIDEO_MIME
- MAX_IMAGE_SIZE_BYTES
- MAX_VIDEO_SIZE_BYTES

Новая страница:
- /admin/card-builder

Что проверять:
- /admin/card-builder
- создание карточки без медиа
- создание карточки с external_url
- создание карточки с upload image
- создание карточки с upload video
- generated code в карточке и в боте
