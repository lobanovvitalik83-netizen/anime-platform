FIX PATCH: репорты не приходят в веб-панель

Причина:
- report handler шёл после fallback handler
- fallback перехватывал текст раньше
- из-за этого обращения в поддержку не создавались

Что исправлено:
- report_support_router перенесён выше fallback_router

Что заменить:
- app/bot/dispatcher.py

После замены:
1. redeploy
2. в боте нажать "Репорт"
3. отправить обычный текст
4. проверить /admin/reports
