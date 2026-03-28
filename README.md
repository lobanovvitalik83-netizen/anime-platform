# Stage 2 - Core + DB

Готово:
- конфиг
- FastAPI app
- PostgreSQL
- SQLAlchemy models
- Alembic migration
- security helpers
- health endpoint

Запуск:
1. pip install -r requirements.txt
2. cp .env.example .env
3. заполнить DATABASE_URL
4. alembic upgrade head
5. python scripts/create_admin.py
6. python run.py

Health:
- GET /health
