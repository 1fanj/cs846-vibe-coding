import pytest
from fastapi.testclient import TestClient
from app import db, logger
from importlib import reload


@pytest.fixture()
def client(tmp_path, monkeypatch):
    dbfile = tmp_path / "test.db"
    monkeypatch.setenv("VIBE_DATABASE_URL", f"sqlite:///{dbfile}")
    import app.db as db_mod
    reload(db_mod)
    import app.main as main_mod
    reload(main_mod)
    main_mod.db.init_db()
    client = TestClient(main_mod.app)
    yield client


def test_ui_served(client):
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Vibe' in r.text


def test_feed_includes_author_username(client):
    # register and post
    r = client.post('/register', json={'username': 'user1', 'password': 'password'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    r2 = client.post('/posts', json={'content': 'hello world'}, headers=headers)
    assert r2.status_code == 200
    feed = client.get('/feed')
    assert feed.status_code == 200
    data = feed.json()
    assert isinstance(data, list) and len(data) >= 1
    p = data[0]
    assert 'author_username' in p and p['author_username'] == 'user1'
