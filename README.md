# Stage 25 - reports fix + helper role + private docs + admin actions + enhanced analytics

Что добавлено:
- Telegram bot:
  - кнопки Поиск по коду / Репорт / Помощь
  - репорты создаются только в режиме Репорт
  - помощь показывает инструкцию и контакт
- live-чаты остаются
- API docs закрыты для всех, кроме superadmin:
  - /docs и /openapi.json отключены
  - private docs доступны по /admin/api-docs
- новая роль:
  - assistant
  - почти как помощник owner: много прав, но не superadmin
- права с человеческими названиями
- отдельное окно действий админов:
  - /admin/admin-actions
  - фильтры по сотруднику, действию, датам, сортировке
- расширенная аналитика:
  - /admin/analytics/advanced
  - топ найденных кодов
  - топ ненайденных кодов
  - активность сотрудников
- улучшенный импорт/экспорт:
  - /admin/import-export/advanced
  - everything.zip
  - отдельные CSV
- улучшены экраны:
  - медиа
  - коды
  - настройки
  - права

Важно по .env:
- TELEGRAM_HELP_CONTACT=...
