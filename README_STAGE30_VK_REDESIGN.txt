Stage 30 - VK-like redesign + achievements

Что добавлено:
- новый VK-like layout: боковая навигация + верхняя панель
- переработаны основные шаблоны:
  login, forgot password, dashboard, media, codes, reports, notifications,
  analytics, profile, people, team, chat_live, settings
- система ачивок:
  - achievements
  - admin_achievements
  - выдача ачивок сотрудникам
  - отображение ачивок в профиле
- forgot password:
  - пользователь отправляет внутренний запрос
  - superadmin получает уведомление
- в архив также включены фиксы репортов Telegram:
  - BIGINT для tg_user_id / tg_chat_id
  - автоматическое приведение существующей БД
  - корректный порядок router-ов и режим репорта

Новые страницы:
- /admin/achievements
- /admin/achievements/new
- /admin/achievements/{id}/edit
- /admin/people/{id}/achievements/grant
- /admin/forgot-password
