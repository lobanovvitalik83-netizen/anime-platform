UI stabilize patch for current anime-platform-main.

Что исправляет:
- убирает ссылки на несуществующие вкладки из левой панели
- показывает разделы по ролям и правам
- чинит /admin за счёт безопасного дашборда
- добавляет работающие /admin/notifications и /admin/admin-actions
- приводит сообщения к нормальному рабочему виду
- делает журнал действий компактнее

Что заменить:
- app/web/routes/admin.py
- app/web/templates/base.html
- app/web/templates/dashboard.html
- app/web/templates/chat_list.html
- app/web/templates/chat_room.html
- app/web/templates/admin_actions.html

После замены:
1. redeploy
2. проверить /admin
3. проверить /admin/profile
4. проверить /admin/chats
5. проверить /admin/notifications
6. проверить /admin/admin-actions
