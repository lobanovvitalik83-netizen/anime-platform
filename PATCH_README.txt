PATCH: Telegram bot menu buttons

Что делает патч:
- добавляет кнопки:
  - Поиск по коду
  - Репорт
  - Помощь
- репорты отправляются только после нажатия кнопки «Репорт»
- помощь показывает инструкцию и контакт
- поиск по коду идёт через кнопку «Поиск по коду»

Что вписать в .env:
TELEGRAM_HELP_CONTACT=УКАЖИ_СВОЙ_КОНТАКТ

Какие файлы заменить:
- .env.example
- app/core/config.py
- app/bot/handlers/start.py
- app/bot/handlers/fallback.py
- app/bot/handlers/code_lookup.py
- app/bot/handlers/report_support.py

Какие новые файлы добавить:
- app/bot/keyboards/main_menu.py
- app/bot/state/session_state.py
