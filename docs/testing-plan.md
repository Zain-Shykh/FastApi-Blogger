# Testing Plan — FastAPI Blogger

Companion to [implementation.md](implementation.md). Goal: exercise every backend endpoint and
every frontend page/flow against a real (non-mocked) backend + database, log whatever breaks in
[testing-log.md](testing-log.md), fix it, and re-test until clean.

## Method

1. **Backend, endpoint-by-endpoint** — via `curl` against a running `fastapi dev`/`uvicorn`
   instance on the project's real Supabase Postgres. Covers happy path, auth requirement, ownership
   checks, and validation errors for each route.
2. **Frontend, flow-by-flow** — via a headless-Chrome script (puppeteer-core against the system
   `google-chrome`) driving the real Vite dev server against the real backend. Covers navigation,
   forms, optimistic UI (likes), and error rendering — the things curl can't verify (does the page
   actually render the data, does a broken request show an error banner instead of a blank screen).
3. All test data (users/posts/comments) is created with an obvious `qatest_` prefix and deleted at
   the end of the run via the API itself (cascades clean up posts/comments/likes).
4. Every failure gets a row in `testing-log.md`: endpoint/page, what was done, expected vs actual,
   status (open/fixed). Fixes are applied, then the specific failing case is re-run and the log
   updated.

## Backend endpoint checklist

### `/users`
- [ ] `POST /users` — register: success, duplicate username (400), duplicate email (400), short
      password (422), invalid email (422)
- [ ] `POST /users/token` — login: success, wrong password (401), unknown email (401)
- [ ] `GET /users/me` — with valid token, without token (401), with garbage token (401)
- [ ] `POST /users/forgot-password` — existing email (202), unknown email (202, no enumeration)
- [ ] `POST /users/reset-password` — invalid token (400)
- [ ] `PATCH /users/me/password` — correct current password, wrong current password (400)
- [ ] `PATCH /users/{id}` — update own username/email, update someone else's (403), duplicate
      username/email (400)
- [ ] `GET /users/{user_id}` — existing (200), missing (404)
- [ ] `DELETE /users/{userid}` — self (204), someone else's (403)
- [ ] `GET /users/{user_id}/posts` — pagination (`skip`/`limit`), unknown user (404)
- [ ] `PATCH /users/{userid}/picture` — valid image, oversized file (400), non-image file (400),
      someone else's account (403)
- [ ] `DELETE /users/{user_id}/picture` — with picture set, with no picture (400)

### `/posts`
- [ ] `GET /posts` — pagination, `likes_count`/`comments_count`/`is_liked_by_me` present and correct
- [ ] `POST /posts` — auth required (401), validation (title/content length)
- [ ] `GET /posts/{id}` — existing, missing (404)
- [ ] `PUT /posts/{id}` / `PATCH /posts/{id}` — owner only (403 for non-owner)
- [ ] `DELETE /posts/{id}` — owner only, cascades comments/likes without error
- [ ] `PATCH /posts/{id}/image` / `DELETE /posts/{id}/image` — owner only
- [ ] `POST /posts/{id}/like` — toggles, `likes_count` updates, `is_liked_by_me` flips
- [ ] `POST /posts/{id}/comments` — returns full `CommentResponse` (no 500), `comments_count` bumps
- [ ] `DELETE /posts/{post_id}/comments/{comment_id}` — owner only, doesn't affect other posts'
      comments (regression check for the old `and`-filter bug)
- [ ] `POST /posts/{post_id}/comments/{comment_id}/replies` — nested correctly, appears in
      `GET /posts/{id}/comments` tree
- [ ] `GET /posts/{id}/comments` — top-level + nested replies, ordering

### `/admin`
- [ ] `GET /admin/metrics` — non-admin gets 403
- [ ] `GET /admin/engagement/top-posts` — ordering by likes
- [ ] `PATCH /admin/users/{user_id}/role` — toggles `is_admin`, self-modification blocked (400)
- [ ] `DELETE /admin/users/{user_id}` — self-ban blocked (400), otherwise cascades
- [ ] `DELETE /admin/posts/{post_id}` — works even with comments (regression check for cascade bug)
- [ ] `DELETE /admin/comments/{comment_id}` — works on replies too

## Frontend flow checklist

- [ ] Home feed loads, paginates, post cards show like/comment counts and thumbnail fallback
- [ ] Register → auto-login → redirected home
- [ ] Login with bad credentials shows error banner (not a crash)
- [ ] Logout clears session and protected links
- [ ] Forgot password → success message shown regardless of whether email exists
- [ ] Create post → redirected to edit view with thumbnail uploader
- [ ] Edit post → save → detail page reflects changes
- [ ] Upload/remove post thumbnail
- [ ] Delete own post → redirected home
- [ ] Like/unlike a post updates count immediately
- [ ] Add a comment, reply to a comment, delete own comment — thread updates without full reload
- [ ] Visiting another user's profile shows their posts, no email leaked, no edit controls
- [ ] Settings: update username/email, change password, upload/remove profile picture, delete
      account (logs out)
- [ ] `ProtectedRoute` redirects anonymous users to `/login` for `/posts/new`, `/posts/:id/edit`,
      `/settings`
- [ ] `AdminRoute` redirects non-admins away from `/admin`
- [ ] Admin dashboard: metrics render, top posts list, delete a post from the list, look up a user
      by ID and toggle role / ban
- [ ] 404 page for unknown routes
