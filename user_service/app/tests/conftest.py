import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from main import app
from app.db import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/app"

@pytest.fixture
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine,expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session
    

    app.dependency_overrides[get_db] = override_get_db

    yield 

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture
async def client(setup_db):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


