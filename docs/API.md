# Vibe API Reference

This document summarizes the primary API endpoints provided by the Vibe microblogging app.

Authentication
- All authenticated endpoints require a Bearer token: `Authorization: Bearer <token>`.
- Obtain a token by registering (`POST /register`) or logging in (`POST /token`).

Endpoints

- `POST /register`
  - Summary: Register a new user
  - Body JSON: `{ "username": "str", "password": "str", "display_name": "str (optional)" }`
  - Response: `{ "access_token": "<token>", "token_type": "bearer" }`

- `POST /token`
  - Summary: User login (OAuth2)
  - Form fields: `username`, `password`
  - Response: `{ "access_token": "<token>", "token_type": "bearer" }`

- `POST /posts`
  - Summary: Create a post
  - Body JSON: `{ "content": "short text up to 280 chars", "parent_id": 123 (optional) }`
  - Notes: Replies allowed one level deep (cannot reply to a reply).
  - Auth: required
  - Response: Post object (see Post schema)

- `GET /feed`
  - Summary: Global feed
  - Query params: `page` (0-indexed, default 0), `page_size` (default 50, max 100)
  - Response: List of Post objects in reverse chronological order

- `POST /posts/{post_id}/like`
  - Summary: Like a post
  - Path param: `post_id`
  - Auth: required
  - Notes: Duplicate likes are rejected.

- `GET /users/{username}`
  - Summary: User profile
  - Path param: `username`
  - Response: Profile object including posts

Schemas (brief)
- Post: `{ id, author_id, content, created_at, parent_id, likes, replies }`
- Profile: `{ id, username, display_name, created_at, posts[] }`
- Token: `{ access_token, token_type }`

Rate limiting
- Mutating endpoints are rate-limited per-user (default 3 requests per 60s). Environment variables `VIBE_RL_MAX` and `VIBE_RL_WINDOW` can override defaults.

OpenAPI & Docs
- The app exposes standard FastAPI docs at `/docs` (Swagger UI) and `/redoc` (ReDoc). The OpenAPI JSON is available at `/openapi.json`.

Examples (curl)

Register and get feed:

```bash
curl -s -X POST "http://127.0.0.1:8000/register" -H "Content-Type: application/json" -d '{"username":"alice","password":"password"}' | jq
# use token returned to create a post
curl -s -X POST "http://127.0.0.1:8000/posts" -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"content":"Hello world"}' | jq
curl -s "http://127.0.0.1:8000/feed?page=0&page_size=10" | jq
```

Notes
- No private messaging, retweets/reposts, or follower graph — feed is global as requested.
- For production, consider switching rate-limiter to Redis and enabling HTTPS behind a reverse proxy.
