# Stage 24 - Live chats, Telegram reports, permissions

Архив включает:
- live-чаты без перезагрузки страницы
- Telegram-like layout для внутренних сообщений
- Telegram reports: сообщения пользователей из бота попадают в админку
- reply в report из админки отправляется именно этому пользователю в Telegram
- новая роль `support`
- дополнительные разрешения на пользователя
- расширенные страницы:
  - /admin/chats-live
  - /admin/reports
  - /admin/team/{id}/permissions
  - /admin/settings/advanced
  - /admin/analytics/advanced
  - /admin/import-export/advanced
  - /admin/editor-tools

Важно:
- live реализован через периодический fetch/polling без refresh страницы
- это не websocket, но сообщения обновляются в реальном времени для оператора
