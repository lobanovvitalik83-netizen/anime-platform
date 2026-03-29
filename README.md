# Stage 22 - External Only Media Storage + Remote Import

В архиве:
- весь stage 21
- BotHost больше не используется как storage для фото/видео карточек
- файлы карточек хранятся только во внешнем storage
- upload файла из формы идёт сразу во внешний storage
- импорт по public/shared URL:
  - Google Drive public link
  - Dropbox shared link
  - обычный CDN / прямой URL
- можно хранить просто внешнюю ссылку без копирования в storage
- если файл был загружен или импортирован системой, при удалении карточки файл удаляется из внешнего storage
- если карточка просто ссылалась на внешний URL без копирования, удаляется только связь в БД

Важно:
- этот этап делает импорт по public/shared URL
- поиск файла по одному только названию внутри Google Drive/Dropbox API без отдельной авторизации сервиса здесь не реализован
- для production рекомендуется S3-compatible storage

Новые поля asset metadata:
- storage_provider
- storage_object_key
- source_url
- source_label
- uploaded_by_system

Новые ENV:
- MEDIA_STORAGE_BACKEND=auto|s3
- S3_ENDPOINT_URL
- S3_ACCESS_KEY_ID
- S3_SECRET_ACCESS_KEY
- S3_BUCKET_NAME
- S3_REGION
- S3_PUBLIC_BASE_URL
- S3_KEY_PREFIX
