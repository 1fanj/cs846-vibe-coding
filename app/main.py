from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
import os
from app import db, models, schemas, auth, logger, ratelimit
from fastapi.staticfiles import StaticFiles

RL_MAX = int(os.environ.get("VIBE_RL_MAX", "3"))
RL_WINDOW = int(os.environ.get("VIBE_RL_WINDOW", "60"))

app = FastAPI(title="Vibe - Microblog")
log = logger.get_logger()

import warnings
# Reduce noisy deprecation warnings from third-party libs that we can't control here.
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*crypt is deprecated.*")

# Serve the simple frontend at /ui
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")


@app.on_event("startup")
def on_startup():
    db.init_db()
    log.info("database_initialized")


@app.post("/register", response_model=schemas.Token, summary="Register a new user", description="Create a new user account and return an access token.")
def register(user: schemas.UserCreate):
    with next(db.get_session()) as session:
        statement = select(models.User).where(models.User.username == user.username)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="username already taken")
        hashed = auth.get_password_hash(user.password)
        new_user = models.User(username=user.username, display_name=user.display_name, hashed_password=hashed)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        access = auth.create_access_token({"sub": new_user.username})
        log.info(f"user_registered: {new_user.username}")
        return {"access_token": access, "token_type": "bearer"}


@app.post("/token", response_model=schemas.Token, summary="User login (OAuth2)", description="Obtain an access token using username and password (form-data). Use returned bearer token for authenticated endpoints.")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with next(db.get_session()) as session:
        user = auth.authenticate_user(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        token = auth.create_access_token({"sub": user.username})
        log.info(f"user_login: {user.username}")
        return {"access_token": token, "token_type": "bearer"}


@app.post("/posts", response_model=schemas.PostOut, summary="Create a post", description="Create a short text post (reply via `parent_id` for one-level replies). Requires Bearer token.")
def create_post(payload: schemas.PostCreate, current_user: models.User = Depends(auth.get_current_user), _rate=Depends(ratelimit.rate_limit(max_requests=RL_MAX, window_seconds=RL_WINDOW))):
    with next(db.get_session()) as session:
        # enforce one-level reply depth
        if payload.parent_id is not None:
            parent = session.get(models.Post, payload.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="parent post not found")
            if parent.parent_id is not None:
                raise HTTPException(status_code=400, detail="cannot reply more than one level deep")
        post = models.Post(author_id=current_user.id, content=payload.content, parent_id=payload.parent_id)
        session.add(post)
        session.commit()
        session.refresh(post)
        log.info(f"post_created: {post.id} by {current_user.username}")
        return _post_out(session, post)

@app.get("/feed", response_model=List[schemas.PostOut], summary="Global feed", description="Return a chronological global feed. Supports pagination via `page` (0-indexed) and `page_size`.")
def feed(page: int = 0, page_size: int = 50, session: Session = Depends(db.get_session)):
    page_size = min(100, max(1, page_size))
    offset = max(0, page) * page_size
    statement = select(models.Post).order_by(models.Post.created_at.desc()).offset(offset).limit(page_size)
    posts = session.exec(statement).all()
    result = [_post_out(session, p) for p in posts]
    return result


@app.post("/posts/{post_id}/like", summary="Like a post", description="Like a post by id. Requires Bearer token. Duplicate likes are rejected.")
def like_post(post_id: int, current_user: models.User = Depends(auth.get_current_user), _rate=Depends(ratelimit.rate_limit(max_requests=RL_MAX, window_seconds=RL_WINDOW))):
    with next(db.get_session()) as session:
        post = session.get(models.Post, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="post not found")
        # prevent duplicate likes
        statement = select(models.Like).where(models.Like.user_id == current_user.id, models.Like.post_id == post_id)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="already liked")
        like = models.Like(user_id=current_user.id, post_id=post_id)
        session.add(like)
        session.commit()
        log.info(f"post_liked: {post_id} by {current_user.username}")
        return {"status": "ok"}


@app.get("/users/{username}", response_model=schemas.ProfileOut, summary="User profile", description="View a user's profile and their posts in chronological order.")
def profile(username: str, session: Session = Depends(db.get_session)):
    statement = select(models.User).where(models.User.username == username)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    # user's posts chronological
    stmt = select(models.Post).where(models.Post.author_id == user.id).order_by(models.Post.created_at.desc())
    posts = session.exec(stmt).all()
    out_posts = [_post_out(session, p) for p in posts]
    profile = schemas.ProfileOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        created_at=user.created_at,
        posts=out_posts,
    )
    return profile


def _post_out(session: Session, post: models.Post) -> schemas.PostOut:
    # count likes
    stmt_likes = select(models.Like).where(models.Like.post_id == post.id)
    likes = session.exec(stmt_likes).all()
    # author username
    author = session.get(models.User, post.author_id)
    author_un = author.username if author else "<deleted>"
    # gather replies one level
    stmt_replies = select(models.Post).where(models.Post.parent_id == post.id).order_by(models.Post.created_at.asc())
    replies = session.exec(stmt_replies).all()
    out_replies = []
    for r in replies:
        stmt_rlikes = select(models.Like).where(models.Like.post_id == r.id)
        rl = session.exec(stmt_rlikes).all()
        out_replies.append(schemas.PostOut(
            id=r.id,
            author_username=(session.get(models.User, r.author_id).username if session.get(models.User, r.author_id) else "<deleted>"),
            author_id=r.author_id,
            content=r.content,
            created_at=r.created_at,
            parent_id=r.parent_id,
            likes=len(rl),
            replies=[],
        ))
    return schemas.PostOut(
        id=post.id,
        author_username=author_un,
        author_id=post.author_id,
        content=post.content,
        created_at=post.created_at,
        parent_id=post.parent_id,
        likes=len(likes),
        replies=out_replies,
    )
