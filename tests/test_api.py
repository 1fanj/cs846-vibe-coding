import pytest
from fastapi.testclient import TestClient
from app import db, logger
from importlib import reload


log = logger.get_logger()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # use a temporary sqlite database for tests
    dbfile = tmp_path / "test.db"
    monkeypatch.setenv("VIBE_DATABASE_URL", f"sqlite:///{dbfile}")
    # reload DB module so engine is created for this test's DB
    import app.db as db_mod
    reload(db_mod)
    # reload app so it picks up the test DB URL
    import app.main as main_mod
    reload(main_mod)
    # clear rate limiter state between tests
    import app.ratelimit as rl
    rl._clear_store_for_tests()
    # initialize DB via the app's db module (ensures same engine)
    main_mod.db.init_db()
    client = TestClient(main_mod.app)
    yield client


def register_user(client, username, password="password"):
    r = client.post("/register", json={"username": username, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def get_token(client, username, password="password"):
    r = client.post("/token", data={"username": username, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login(client):
    token = register_user(client, "alice")
    assert token
    got = get_token(client, "alice")
    assert got


def test_post_and_feed_and_profile(client):
    t = register_user(client, "bob")
    # create posts
    r = client.post("/posts", json={"content": "Hello world"}, headers=auth_headers(t))
    assert r.status_code == 200
    post = r.json()
    assert post["content"] if isinstance(post, dict) else True
    # create reply
    r2 = client.post("/posts", json={"content": "reply", "parent_id": post["id"]}, headers=auth_headers(t))
    assert r2.status_code == 200
    # feed
    r3 = client.get("/feed")
    assert r3.status_code == 200
    data = r3.json()
    assert isinstance(data, list)
    # profile
    r4 = client.get(f"/users/bob")
    assert r4.status_code == 200
    profile = r4.json()
    assert profile["username"] == "bob"


def test_like(client):
    t1 = register_user(client, "carol")
    t2 = register_user(client, "dave")
    # carol posts
    r = client.post("/posts", json={"content": "Carol post"}, headers=auth_headers(t1))
    pid = r.json()["id"]
    # dave likes
    r2 = client.post(f"/posts/{pid}/like", headers=auth_headers(t2))
    assert r2.status_code == 200
    # liking again should fail
    r3 = client.post(f"/posts/{pid}/like", headers=auth_headers(t2))
    assert r3.status_code == 400
    # like count visible in feed
    r4 = client.get("/feed")
    assert r4.status_code == 200
    feed = r4.json()
    found = [p for p in feed if p["id"] == pid]
    assert found and found[0]["likes"] == 1


def test_reply_depth_limit(client):
    t = register_user(client, "erin")
    r = client.post("/posts", json={"content": "root"}, headers=auth_headers(t))
    root = r.json()["id"]
    r2 = client.post("/posts", json={"content": "child", "parent_id": root}, headers=auth_headers(t))
    child = r2.json()["id"]
    # attempt to reply to child (depth 2) should fail
    r3 = client.post("/posts", json={"content": "grandchild", "parent_id": child}, headers=auth_headers(t))
    assert r3.status_code == 400
    log.info("tests_completed")


def test_pagination(client):
    # create a dedicated app instance with high RL for this test
    import os
    from importlib import reload
    os.environ["VIBE_RL_MAX"] = "1000"
    import app.db as db_mod
    reload(db_mod)
    import app.main as main_mod
    reload(main_mod)
    import app.ratelimit as rl
    rl._clear_store_for_tests()
    main_mod.db.init_db()
    from fastapi.testclient import TestClient as LocalClient
    local = LocalClient(main_mod.app)

    # create 25 posts across several users to avoid per-user rate limits
    tokens = [
        (lambda tok=register_user(local, f"pu{i}"): tok)()
        for i in range(5)
    ]
    for i in range(25):
        who = tokens[i % len(tokens)]
        r = local.post("/posts", json={"content": f"post {i}"}, headers=auth_headers(who))
        assert r.status_code == 200
    # page 0, size 10
    r0 = local.get("/feed", params={"page": 0, "page_size": 10})
    assert r0.status_code == 200
    p0 = r0.json()
    assert len(p0) == 10
    # page 2 (third page) should have 5 posts
    r2 = local.get("/feed", params={"page": 2, "page_size": 10})
    assert r2.status_code == 200
    p2 = r2.json()
    assert len(p2) == 5
    local.close()


def test_rate_limit_hits(client):
    # explicitly set rl params and reload app so limit takes effect
    import os
    from importlib import reload
    # create a dedicated app instance with a low RL for this test
    os.environ["VIBE_RL_MAX"] = "3"
    import app.db as db_mod
    reload(db_mod)
    import app.main as main_mod
    reload(main_mod)
    import app.ratelimit as rl
    rl._clear_store_for_tests()
    main_mod.db.init_db()
    from fastapi.testclient import TestClient as LocalClient
    local = LocalClient(main_mod.app)
    # register and exercise rate limit
    t = register_user(local, "rluser")
    for i in range(3):
        r = local.post("/posts", json={"content": f"rl {i}"}, headers=auth_headers(t))
        assert r.status_code == 200
    r4 = local.post("/posts", json={"content": "rl blocked"}, headers=auth_headers(t))
    assert r4.status_code == 429
    local.close()
