# FastAPI Blogger

A blog platform with a FastAPI backend and a React (Vite) frontend.

```
Blog_Project/
├── backend/    FastAPI app (SQLAlchemy async, Postgres, JWT auth, S3-compatible image storage)
├── frontend/   React + Vite + Tailwind CSS + React Router + Context API
├── docs/       Design notes, implementation plan (see docs/implementation.md)
├── requirements.txt
└── .gitignore
```

## Features

- User registration, login (JWT), profile pictures, password reset via email
- Posts: create/edit/delete, thumbnail images, pagination
- Likes and threaded comments/replies
- Admin dashboard: platform metrics, top posts, user role management, content moderation

## Backend setup

```bash
cd backend
python3 -m venv myenv
source myenv/bin/activate
pip install -r ../requirements.txt
```

Create `backend/.env` with:

```
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>/<db>
SECRET_KEY=<random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MAIL_SERVER=<smtp-host>
MAIL_PORT=587
MAIL_USERNAME=<smtp-user>
MAIL_PASSWORD=<smtp-password>
MAIL_FROM=noreply@example.com
MAIL_USE_TLS=true

FRONTEND_URL=http://localhost:5173

S3_BUCKET_NAME=<bucket>
S3_REGION=<region>
S3_ACCESS_KEY_ID=<key>
S3_SECRET_ACCESS_KEY=<secret>
S3_ENDPOINT_URL=<endpoint, e.g. Supabase storage URL>
```

Run migrations and start the API:

```bash
alembic upgrade head
fastapi dev main.py
```

The API runs at `http://localhost:8000` (interactive docs at `/docs`).

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env` with:

```
VITE_API_URL=http://localhost:8000
```

The app runs at `http://localhost:5173`.

## Docs

See [docs/implementation.md](docs/implementation.md) for the full API inventory, known-bug audit,
and frontend architecture.
