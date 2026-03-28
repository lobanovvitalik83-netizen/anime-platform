HOTFIX: bcrypt password length fix

Причина ошибки:
bcrypt не принимает пароль длиннее 72 байт.

Что исправлено:
- если пароль длиннее 72 байт, перед bcrypt он нормализуется через SHA-256 hex
- verify использует ту же нормализацию

Что сделать:
1. заменить файл app/core/security.py
2. commit + push
3. redeploy
4. снова вызвать POST /api/auth/bootstrap-default-admin
