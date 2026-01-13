# Vibe — Minimal Microblog

Tiny Twitter-like microblog with a minimal single-page UI and a small API.

Quick start
-----------
1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies and run the server:

```bash
pip install -r requirements.txt
PYTHONPATH=. ./.venv/bin/uvicorn app.main:app --reload
```

Open the UI at: http://127.0.0.1:8000/ui/

API highlights
--------------
- `POST /register` — create a user and receive a bearer token
- `POST /token` — login (form data) and obtain a bearer token
- `POST /posts` — create a post (requires bearer token)
- `GET /feed` — global chronological feed (supports `page`, `page_size`)
- `POST /posts/{id}/like` — like a post (requires bearer token)
- `GET /users/{username}` — view a user's profile and posts

Examples
--------
- Run the bundled curl examples (auto-extracts token):

```bash
bash scripts/client_examples.sh
```

- Python client example:

```bash
PYTHONPATH=. python3 scripts/python_client.py
```

- Generate static OpenAPI specs:

```bash
PYTHONPATH=. python3 scripts/generate_openapi.py
```

Logs
----
Logs are written to `logs/app.log.json` and `logs/app.log.md`.

Password hashing migration
--------------------------
The app uses `argon2` for password hashing. Argon2 hashes are not compatible with bcrypt/pbkdf2. For existing user databases, re-hash passwords on successful login or require users to reset passwords.

License
-------
See the repository `LICENSE` for terms.
