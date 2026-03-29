# Stage 17 - Users / Password Reset / Profiles

В архиве:
- весь stage 16
- полное управление пользователями
- создание пользователя с ручным паролем или автогенерацией
- логин задаётся только при создании и больше не меняется
- разовый показ логина/пароля после создания
- сброс пароля с генерацией нового пароля
- разовый показ нового пароля после сброса
- профиль пользователя
- аватар
- full name / должность / about
- смена своего пароля
- блокировка / разблокировка по ролям

Правила ролей:
- owner = superadmin
- admin может управлять только editor
- superadmin может управлять admin и editor
- никто не может блокировать сам себя через team management
- superadmin не управляет другими superadmin через team management

Новые страницы:
- /admin/team
- /admin/team/new
- /admin/team/{id}/edit
- /admin/profile

Новые ENV:
- DATA_DIR=/app/data
- MAX_AVATAR_SIZE_BYTES=2097152
