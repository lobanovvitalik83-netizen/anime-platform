Stage 31 complete package

Что добавлено:
- achievements:
  - models, repository, service
  - создание / редактирование / удаление
  - выдача сотруднику
  - отображение в профиле и профиле сотрудника
- forgot password:
  - страница /admin/forgot-password
  - внутренний запрос на сброс пароля через уведомление администрации
- product-like redesign:
  - новая base layout с боковой навигацией и верхней панелью
  - новые login / forgot password / dashboard / profile / people / person profile templates
- reports fix:
  - BIGINT для tg_user_id / tg_chat_id
  - runtime schema upgrade
  - правильный порядок bot routers
  - report handler не конфликтует с lookup/buttons

Проверить:
- /admin/login
- /admin/forgot-password
- /admin
- /admin/profile
- /admin/people
- /admin/people/{id}
- /admin/achievements
- /admin/people/{id}/achievements/grant
- Telegram report mode
