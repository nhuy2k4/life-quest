# LifeQuest Backend Setup (Windows)

## 1. Create Python Virtual Environment

```powershell
# In project root
your_python_path\python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Install Dependencies

```powershell
pip install --upgrade pip
pip install fastapi uvicorn[standard] pydantic sqlalchemy asyncpg alembic python-dotenv redis celery[redis] cloudinary google-cloud-vision python-multipart bcrypt pyjwt requests
```

## 3. Docker Compose (PostgreSQL + Redis)

```powershell
docker-compose up -d
```

## 4. Alembic Migrations

```powershell
alembic upgrade head
```

## 5. Start FastAPI Server

```powershell
uvicorn app.main:app --reload
```

## 6. Start Celery Worker

```powershell
celery -A app.workers.celery_app.celery worker --loglevel=info
```

---

## .env Example

```
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgresql@localhost:5432/lifequest

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Google Vision
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-vision.json
```

---

## PowerShell/CMD Setup Script

```powershell
# 1. Create venv
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install fastapi uvicorn[standard] pydantic sqlalchemy asyncpg alembic python-dotenv redis celery[redis] cloudinary google-cloud-vision python-multipart bcrypt pyjwt requests

# 3. Start Docker
start docker
# or manually: docker-compose up -d

# 4. Run migrations
alembic upgrade head

# 5. Start FastAPI
uvicorn app.main:app --reload

# 6. Start Celery
celery -A app.workers.celery_app.celery worker --loglevel=info
```

## Link swagger: http://localhost:8000/docs#/

---

## Notes

- Ensure Docker Desktop is running before `docker-compose up -d`.
- Update `.env` with your actual secrets and credentials.
- All commands are Windows/PowerShell compatible.
