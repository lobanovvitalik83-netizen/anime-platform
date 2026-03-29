# Stage 23 - Yandex Disk media backend

В архиве:
- весь stage 22
- backend `yandex_disk`
- upload файла из карточки сразу на Яндекс Диск
- import по прямому URL с копированием на Яндекс Диск
- хранение только metadata в BotHost
- удаление файла с Яндекс Диска при удалении карточки, если файл был загружен системой
- публичный proxy/redirect route для показа картинки/видео из Яндекс Диска
- авто-создание рабочих папок приложения на Диске

ENV:
- MEDIA_STORAGE_BACKEND=yandex_disk
- PUBLIC_BASE_URL=https://твой-домен
- YANDEX_DISK_OAUTH_TOKEN=...
- YANDEX_DISK_BASE_PATH=app:/media-bridge

Что создаётся автоматически:
- `app:/media-bridge`
- `app:/media-bridge/image`
- `app:/media-bridge/video`

Как это работает:
- файл грузится на Яндекс Диск
- в БД хранится только путь файла на Диске + metadata
- для просмотра система отдаёт ссылку на свой публичный route
- этот route на лету получает download href из Yandex Disk API и делает redirect к файлу
