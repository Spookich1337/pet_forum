import pytest
from fastapi.testclient import TestClient

from src.core.main import app

client = TestClient(app)


def assert_ok(response):
    # допускаем любые "нормальные" ответы, кроме 404 и 500
    assert response.status_code not in (404, 500)


def test_root():
    r = client.get("/")
    assert_ok(r)


def test_users():
    r = client.get("/users")
    assert_ok(r)


def test_user_by_id():
    r = client.get("/users/1")
    assert_ok(r)


def test_posts():
    r = client.get("/posts")
    assert_ok(r)


def test_create_post():
    r = client.post("/posts", json={
        "title": "test",
        "text": "test"
    })
    assert_ok(r)
