from httpx import AsyncClient

async def test_register(client: AsyncClient):
    res = await client.post("/user/users", json={
        "email": "test@gmail.com",
        "password": "secret123"
    })
    assert res.status_code == 200
    assert res.json()["email"] == "test@gmail.com"

async def test_register_duplicate(client: AsyncClient):
    data = {"email": "test@gmail.com", "password": "secret123"}
    await client.post("/user/users", json=data)
    res = await client.post("/user/users", json=data)  # второй раз
    assert res.status_code == 409

async def test_login(client: AsyncClient):
    await client.post("/user/users", json={
        "email": "test@gmail.com",
        "password": "secret123"
    })
    res = await client.post("/user/login", data={  # data вместо json
        "username": "test@gmail.com",  # OAuth2 использует username а не email
        "password": "secret123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

async def test_me(client: AsyncClient):
    # регистрация
    await client.post("/user/users", json={
        "email": "test@gmail.com",
        "password": "secret123"
    })
    # логин
    res = await client.post("/user/login", data={  # data вместо json
        "username": "test@gmail.com",  # OAuth2 использует username а не email
        "password": "secret123"
    })
    token = res.json()["access_token"]

    # запрос /me с токеном
    res = await client.get("/user/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 200
    assert res.json()["email"] == "test@gmail.com"


async def test_register_invalid_email(client:AsyncClient):
    res = await client.post("/user/users", json={
        "email": "test.com",
        "password": "secret123"
    })

    assert res.status_code == 422

async def test_login_wrong_password(client:AsyncClient):

    res = await client.post("/user/login", data={  # data вместо json
        "username": "test@gmail.com",  # OAuth2 использует username а не email
        "password": "secret123"
    })

    assert res.status_code == 401


async def test_me_no_token(client:AsyncClient):

    res = await client.get("/user/me", headers={
        "Authorization": f"Bearer "
    })

    assert res.status_code == 401