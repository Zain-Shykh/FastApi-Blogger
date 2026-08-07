# FastAPI Blogger — Monorepo Implementation Plan

Status: living document. Written after a full read-through of the existing `backend/` codebase.
Repo: https://github.com/Zain-Shykh/FastApi-Blogger

## 1. Goal

Turn the existing FastAPI-only backend into a monorepo:

```
Blog_Project/
├── backend/    (existing FastAPI app, some bugs fixed — see §3)
├── frontend/   (new: React + Vite + Tailwind + React Router + Context API)
├── docs/       (this file and future notes)
├── .gitignore
├── README.md
└── requirements.txt   (re-export of backend/requirements.txt at root for convenience)
```

No backend features are being invented. The frontend is built strictly against the endpoints
that already exist in `backend/routers/*.py`, plus the two small read additions listed in §3.2
that were explicitly approved (comments couldn't otherwise be displayed at all).

## 2. Backend audit — as found

Stack: FastAPI, SQLAlchemy 2.0 (async, `postgresql+psycopg`), Alembic migrations, JWT auth
(`pyjwt` + `pwdlib`/argon2), Supabase/S3-compatible object storage for images (`boto3`), email via
`aiosmtplib` + Jinja2 templates.

Domain model (`backend/models.py`): `User`, `Post`, `PasswordResetToken`, `Like`, `Comment`
(self-referential for replies).

### 2.1 Endpoint inventory

**`/users`** (`backend/routers/users.py`)
| Method & Path | Auth | Purpose |
|---|---|---|
| POST /users | – | Register |
| POST /users/token | – | Login (OAuth2 password form; `username` field = email) |
| GET /users/me | ✓ | Current user |
| POST /users/forgot-password | – | Request password reset email |
| POST /users/reset-password | – | Consume reset token |
| PATCH /users/me/password | ✓ | Change password (knows current password) |
| PATCH /users/{id} | ✓ (self) | Update username/email |
| GET /users/{user_id} | – | Public profile |
| DELETE /users/{userid} | ✓ (self) | Delete own account |
| GET /users/{user_id}/posts | – | Paginated posts by user |
| PATCH /users/{userid}/picture | ✓ (self) | Upload profile picture |
| DELETE /users/{user_id}/picture | ✓ (self) | Remove profile picture |

**`/posts`** (`backend/routers/posts.py`)
| Method & Path | Auth | Purpose |
|---|---|---|
| GET /posts | – | Paginated feed |
| POST /posts | ✓ | Create post |
| GET /posts/{id} | – | Post detail |
| PUT /posts/{id} | ✓ (owner) | Full update |
| PATCH /posts/{id} | ✓ (owner) | Partial update |
| DELETE /posts/{id} | ✓ (owner) | Delete |
| PATCH /posts/{id}/image | ✓ (owner) | Upload thumbnail |
| DELETE /posts/{id}/image | ✓ (owner) | Remove thumbnail |
| POST /posts/{id}/like | ✓ | Toggle like |
| POST /posts/{id}/comments | ✓ | Add comment |
| DELETE /posts/{post_id}/comments/{comment_id} | ✓ (owner) | Delete comment |
| POST /posts/{post_id}/comments/{comment_id}/replies | ✓ | Reply to comment |

**`/admin`** (`backend/routers/admin.py`) — exists in code but **not mounted** in `main.py` (bug, fixed in §3.1)
| Method & Path | Auth | Purpose |
|---|---|---|
| GET /admin/metrics | admin | Platform counts |
| GET /admin/engagement/top-posts | admin | Top posts by likes |
| PATCH /admin/users/{user_id}/role | admin | Toggle admin flag |
| DELETE /admin/users/{user_id} | admin | Ban/wipe user |
| DELETE /admin/posts/{post_id} | admin | Force-delete post |
| DELETE /admin/comments/{comment_id} | admin | Force-delete comment |

### 2.2 Bugs found (confirmed by reading source, one confirmed via `starlette.staticfiles` source)

1. **App cannot start at all.** `main.py` does `app.mount("/static", StaticFiles(directory="static"), ...)`.
   No `static/` directory exists (only `media/`), and Starlette's `StaticFiles.__init__` raises
   `RuntimeError` immediately when `check_dir=True` (the default) and the directory is missing.
2. **`GET /users/{user_id}`**: route declares `{user_id}`, handler param is `userid` → FastAPI can't
   bind it from the path (name mismatch), so the id silently becomes a required query param.
3. **`DELETE /users/{userid}`**: route declares `{userid}`, handler param is `id` → same class of bug.
4. **`PATCH /users/{userid}/picture`**: route declares `{userid}`, handler param is `user_id` → same
   bug, **plus** `if current_user != user_id` compares a `User` object to an `int`, which is always
   true, i.e. the ownership check can never pass.
5. **`DELETE /posts/{post_id}/comments/{comment_id}`**: filter is
   `models.Comment.id == comment_id and models.Comment.post_id == post_id`. Python `and` short-circuits
   on the first SQLAlchemy `ColumnElement`, which is not a boolean — this does not filter by `post_id`
   at all (and depending on SQLAlchemy version can raise instead of filtering).
6. **Password reset email never renders.** `email_utils.send_password_reset_email` calls
   `templates.env.get_template("password_reset_email.html")`, but the actual file is
   `backend/templates/email/password_reset.html` — wrong path and wrong filename.
7. **Admin router never mounted** — see table above.

### 2.2b Additional bugs found during integration testing (not visible from static reading)

These only surfaced when actually running the app end-to-end against a real database:

8. **Deleting any post that has comments crashed with `IntegrityError`.** `Post.comments` (and
   `Post.likes`) had no `cascade="all, delete-orphan"`, unlike the equivalent relationships on
   `User`. Deleting a post tried to null out `comments.post_id`, which is `NOT NULL`. Fixed in
   `models.py`.
9. **`POST /posts/{id}/comments` and `POST /posts/{post_id}/comments/{comment_id}/replies` always
   returned 500.** `CommentResponse` serializes a `replies` field, but the newly created ORM comment
   was only refreshed with `attribute_names=["user"]`; accessing `.replies` on an async session
   triggers an implicit lazy-load, which SQLAlchemy's async engine forbids
   (`MissingGreenlet`/similar). Fixed by constructing the `CommentResponse` explicitly with
   `replies=[]` (correct for a just-created comment) instead of returning the raw ORM object.
10. **`UserPublic` had no `is_admin` field**, so `PATCH /admin/users/{user_id}/role` (which mutates
    exactly that field) couldn't report the result. Added `is_admin: bool` to `UserPublic`.

All ten fixes were verified with live curl-based integration tests against the project's actual
Supabase Postgres instance (register → login → CRUD posts → like/comment/reply → delete with
cascades → admin metrics/role-toggle/ban/delete → cleanup). Profile-picture upload and
forgot-password were verified up to the point of calling S3 / SMTP respectively (both correctly
reach those calls now); the S3 and SMTP failures seen in this sandbox are credential/network
issues in the test environment, not code bugs.

### 2.3 Fixes to apply (approved)

- Change the static mount to serve `media/` (or drop the mount — images are actually served from
  S3-compatible storage per `imageutils.py`; local `media/` only held a `default.jpg` placeholder
  that was never committed). Decision: mount `/media` → `media/` so the hardcoded fallback
  `image_path` defaults (`/media/profile_pics/default.jpg`, `/media/thumbnails/default.jpg`) resolve
  to *something* instead of 404ing the whole app.
- Fix the three path/handler param-name mismatches in `users.py` (rename handler params to match
  the route path params) and fix the `current_user != user_id` logic bug.
- Fix the comment delete filter to `models.Comment.id == comment_id, models.Comment.post_id == post_id`
  (comma = AND in SQLAlchemy `.where()`).
- Fix the email template path to `email/password_reset.html`.
- Mount `admin.router` in `main.py`.

### 2.4 Minimal read-side additions (approved, needed for comments/likes UI to function)

The `Like`/`Comment` models and write endpoints exist, but there is no way to read them back:

- Add `GET /posts/{id}/comments` — returns top-level comments (with nested `replies`) for a post.
- Add `likes_count: int`, `comments_count: int`, `is_liked_by_me: bool` to `PostResponse` (computed
  in the router, not stored columns) so post cards/detail pages can render like counts and comment
  counts without extra round-trips, and so the UI knows whether to show "like" vs "unlike".

No new models, tables, or migrations required — these are read projections over existing data.
`is_liked_by_me` requires the current user when available; for anonymous requests it's `false`.

## 3. Frontend plan

### 3.1 Stack (per user constraint: nothing beyond these)

- Vite + React (JavaScript, not TypeScript, to match backend's dynamic/lightweight style — can be
  reconsidered)
- React Router (v6+) for routing
- Tailwind CSS for styling
- React Context API for state (no Redux/Zustand/React Query) — `AuthContext` for the logged-in user
  + JWT, plain `fetch` wrapper for API calls with local component state / `useEffect` for data
  fetching per page.

### 3.2 API client

`frontend/src/api/client.js` — thin `fetch` wrapper:
- Base URL from `VITE_API_URL` env var (default `http://localhost:8000`).
- Attaches `Authorization: Bearer <token>` when a token is present (token kept in `localStorage` +
  mirrored in `AuthContext`).
- Throws a normalized `ApiError { status, detail }` on non-2xx so pages can render backend
  validation/detail messages.

### 3.3 Routes

| Path | Page | Notes |
|---|---|---|
| `/` | Home / post feed | `GET /posts`, paginated |
| `/login` | Login | `POST /users/token` |
| `/register` | Register | `POST /users` |
| `/forgot-password` | Forgot password | `POST /users/forgot-password` |
| `/reset-password` | Reset password | reads `?token=`, `POST /users/reset-password` |
| `/posts/:id` | Post detail | post + comments + like button |
| `/posts/new` | Create post | protected |
| `/posts/:id/edit` | Edit post | protected, owner-only (owner check mirrored client-side, enforced server-side) |
| `/users/:id` | Public profile + their posts | `GET /users/:id`, `GET /users/:id/posts` |
| `/settings` | Account settings | change username/email/password, profile picture, delete account |
| `/admin` | Admin dashboard | protected, `is_admin` only — metrics, top posts, user/post/comment moderation |

### 3.4 Components (indicative, not exhaustive)

- `Layout` (nav bar with auth-aware links, logout)
- `ProtectedRoute` / `AdminRoute` wrappers using `AuthContext`
- `PostCard`, `PostList`, `Pagination`
- `PostForm` (create/edit, title+content, thumbnail upload)
- `CommentThread`, `CommentForm` (recursive for replies)
- `LikeButton`
- `ProfilePictureUploader`
- `Toast`/inline error banner fed by `ApiError`

### 3.5 Auth flow

- `AuthContext` holds `{ user, token, login(), logout(), refreshMe() }`.
- On app load, if a token exists in `localStorage`, call `GET /users/me` to hydrate `user`; on 401,
  clear the token.
- Login stores `access_token` from `/users/token`, then fetches `/users/me`.
- No refresh-token endpoint exists in the backend, so session simply expires with the JWT
  (`ACCESS_TOKEN_EXPIRE_MINUTES`) and the user is redirected to `/login` on a 401.

## 4. Repo/monorepo cleanup

- `.git` currently lives in `backend/` (that's why GitHub still shows the old flat layout). Move it
  to the project root and commit the new `backend/frontend/docs` layout there. History is preserved;
  file paths change (git will detect the moves as renames in the diff).
- Root `.gitignore` covers: `**/node_modules/`, `**/__pycache__/`, `**/myenv/`, `**/.venv/`, `*.db`,
  `.env`, `.env.local`, `**/.mypy_cache/`, `backend/media/*` (keep `.gitkeep`), frontend `dist/`.
- Root `requirements.txt`: pinned to versions currently installed in `backend/myenv` (this project
  never had one before).
- Root `README.md`: project overview, monorepo layout, how to run backend, how to run frontend,
  env var reference (names only, no secrets).

## 5. Out of scope / explicitly not built

- No refresh tokens, no OAuth/social login (backend doesn't have them).
- No comment editing (backend has no `PATCH` for comments, only create/delete/reply).
- No search/tags/categories (no such fields on `Post`).
- No websockets/real-time notifications.
- No CI/CD pipeline changes.
