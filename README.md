# Vibe - Microblog (Minimal Twitter-like)

Quick startup:

1. Create a virtualenv and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
uvicorn app.main:app --reload
```

API highlights:
- `POST /register` register and receive token
- `POST /token` login with form data
- `POST /posts` create post (bearer token)
# Vibe - Microblog

Minimal microblogging app with a tiny single-page UI.

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

Open the UI: http://127.0.0.1:8000/ui/

Key API endpoints
-----------------
- `POST /register` — create a user and receive a bearer token
- `POST /token` — login (form data) to obtain a bearer token
- `POST /posts` — create a post (requires bearer token)
- `GET /feed` — global chronological feed (supports `page`, `page_size`)
- `POST /posts/{id}/like` — like a post (requires bearer token)
- `GET /users/{username}` — view a user's profile and posts

Examples
--------
- Curl examples (auto-extracts token):
	```bash
	bash scripts/client_examples.sh
	```
- Python client:
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
The app uses `argon2` for password hashing. Argon2 hashes are not compatible with bcrypt/pbkdf2. If you have an existing user database, migrate passwords by re-hashing on successful login or require users to reset passwords.
