"""
Tests cho phần Authentication — LifeQuest Backend

Chạy: pytest tests/test_auth.py -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.deps.db import get_db
from app.main import app

# ── Test database (SQLite in-memory cho tốc độ) ───────────────────────────────
# Lưu ý: SQLite không hỗ trợ ARRAY và JSONB đầy đủ.
# Dùng PostgreSQL test DB cho môi trường CI production.
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_lifequest.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Tạo tất cả bảng trước khi chạy tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client với dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass1",
}


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    """Tạo user đã đăng ký sẵn."""
    response = await client.post("/api/v1/auth/register", json=VALID_USER)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def tokens(client: AsyncClient, registered_user):
    """Login và trả về tokens."""
    response = await client.post("/api/v1/auth/login", json={
        "username": VALID_USER["username"],
        "password": VALID_USER["password"],
    })
    assert response.status_code == 200
    return response.json()


# ── Register Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Đăng ký thành công → 201, trả UserMeResponse."""
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePass1",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert data["onboarding_completed"] is False
    assert data["xp"] == 0
    assert "password_hash" not in data  # Không expose password


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, registered_user):
    """Email đã tồn tại → 409 Conflict."""
    payload = {
        "username": "different_user",
        "email": VALID_USER["email"],   # email trùng
        "password": "SecurePass1",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "Email" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, registered_user):
    """Username đã tồn tại → 409 Conflict."""
    payload = {
        "username": VALID_USER["username"],  # username trùng
        "email": "different@example.com",
        "password": "SecurePass1",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "Username" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Mật khẩu yếu (không có chữ hoa/số) → 422 Validation Error."""
    payload = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "password",  # không có chữ hoa & số
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username(client: AsyncClient):
    """Username có ký tự đặc biệt → 422."""
    payload = {
        "username": "user@name!",      # ký tự không hợp lệ
        "email": "invalid@example.com",
        "password": "SecurePass1",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ── Login Tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user):
    """Login thành công → 200, có access_token và refresh_token."""
    response = await client.post("/api/v1/auth/login", json={
        "username": VALID_USER["username"],
        "password": VALID_USER["password"],
    })
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "onboarding_completed" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, registered_user):
    """Sai mật khẩu → 401, không tiết lộ username có tồn tại không."""
    response = await client.post("/api/v1/auth/login", json={
        "username": VALID_USER["username"],
        "password": "WrongPassword1",
    })
    assert response.status_code == 401
    # Anti username-enumeration: cùng 1 message cho sai username và sai password
    assert "Username hoặc mật khẩu" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_username(client: AsyncClient):
    """Username không tồn tại → 401, cùng message với sai password (anti-enumeration)."""
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent_user",
        "password": "SecurePass1",
    })
    assert response.status_code == 401
    assert "Username hoặc mật khẩu" in response.json()["detail"]


# ── Refresh Tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, tokens):
    """Refresh token hợp lệ → 200, access token mới."""
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Token mới phải khác token cũ (rotation)
    assert data["access_token"] != tokens["access_token"]
    assert data["refresh_token"] != tokens["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Refresh token không hợp lệ → 401."""
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid_fake_token_12345",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_used_token_rejected(client: AsyncClient, tokens):
    """Dùng refresh token đã dùng 1 lần → 401 (token rotation bảo vệ reuse)."""
    old_refresh = tokens["refresh_token"]

    # Lần đầu refresh — OK
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert response.status_code == 200

    # Dùng lại token cũ — phải bị từ chối
    response2 = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert response2.status_code == 401


# ── Logout Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, tokens):
    """Logout → 204 No Content."""
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_access_token_blacklisted_after_logout(client: AsyncClient, tokens):
    """Sau logout, access token cũ không dùng được nữa → 401."""
    # Logout
    await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    # Thử dùng access token cũ — phải bị rejected
    # (cần endpoint protected để test — dùng /api/v1/auth/logout lần 2)
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "any_token"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 401


# ── Auth Guard Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client: AsyncClient):
    """Gọi endpoint cần auth mà không có token → 401."""
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "dummy"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_invalid_token(client: AsyncClient):
    """Gọi endpoint cần auth với token giả → 401."""
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "dummy"},
        headers={"Authorization": "Bearer fake.jwt.token"},
    )
    assert response.status_code == 401
