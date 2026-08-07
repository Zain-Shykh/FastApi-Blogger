# Testing Log — FastAPI Blogger

Executed against [testing-plan.md](testing-plan.md). Backend tested via `curl` against a running
`uvicorn` instance on the project's real Supabase Postgres. Frontend tested via a headless-Chrome
script (puppeteer-core) driving the real Vite dev server against the real backend — real clicks,
real forms, real network requests, no mocking.

## Round 1 — initial run

**Backend (curl):** 62 passed / 4 failed. All 4 failures were the same S3 upload path (post
thumbnail upload/delete, profile picture upload/delete) — see "Known limitation" below.

**Frontend (browser):** every single flow past the home page failed. Register, login, and every
other API call from the browser errored out.

### Error 1 — CORS not configured (critical, found only by browser testing)

- **Symptom:** `Access to fetch at 'http://localhost:8123/users' from origin
  'http://localhost:5174' has been blocked by CORS policy: Response to preflight request doesn't
  pass access control check: No 'Access-Control-Allow-Origin' header is present.` Every frontend
  API call failed identically.
- **Why curl testing missed it:** CORS is a browser-enforced restriction, not a server-side
  validation — curl (and the earlier backend-only test round, and the original manual code review)
  never exercises it, so this was invisible until a real browser drove the real frontend against
  the real backend.
- **Root cause:** `backend/main.py` never added `CORSMiddleware`. The FastAPI app had zero CORS
  configuration, so it rejected every cross-origin request by default — meaning the React frontend
  could never talk to the backend at all, from any browser, regardless of how correct the rest of
  the code was.
- **Fix:** added `CORSMiddleware` to `main.py`, allowing `settings.frontend_url` (the configured
  production frontend origin) plus any `http://localhost:<port>` origin (covers Vite's dev server,
  which doesn't use a fixed port).
- **Status:** Fixed. Re-verified: preflight `OPTIONS /users` now returns
  `access-control-allow-origin: http://localhost:5174` and all subsequent frontend flows passed.

### Error 2 — test script: comment-delete click hit the wrong "Delete" button

- **Symptom:** E2E run hung indefinitely (`Runtime.callFunctionOn timed out`) on the "delete own
  comment" step.
- **Root cause:** the test script selected the *first* button with text "Delete", which was the
  post's own delete button (behind a native `window.confirm()`), not the comment's delete link.
  Puppeteer had no `dialog` handler attached, so the confirm dialog blocked the page indefinitely.
- **This was a test-script bug, not an app bug** — the app's confirm-before-destructive-action UX
  is correct.
- **Status:** Fixed test script (scoped the selector to the comment's distinct CSS class, added a
  global `dialog` auto-accept handler). Re-run passed.

### Error 3 — test script: username field not actually cleared before retyping

- **Symptom:** `PATCH /users/{id}` returned `422 String should have at most 50 characters` and the
  settings-update assertion failed.
- **Root cause:** the test script used a triple-click + Backspace to clear the username field
  before typing a new value; the selection didn't reliably take, so the new value was appended to
  the old one instead of replacing it, producing a 51+ character string.
- **This was a test-script bug, not an app bug** — the backend correctly rejected the oversized
  input with a validation error instead of silently truncating or crashing.
- **Status:** Fixed test script (clear the input via the native value setter + `input` event
  before typing, which is the reliable way to clear a React-controlled input). Re-run passed.

## Round 2 — after fixes

**Backend:** 62 passed / 4 failed (same 4, S3-related, see below) + 9/9 admin-specific checks
passed after promoting a test user to admin = **71 passed / 4 failed**.

**Frontend:** 27/27 core flow checks passed. 12/12 admin-dashboard checks passed (metrics render,
top posts list, user lookup, role toggle both directions, in-place moderation from a user's
profile page, ban flow, banned user can no longer log in).

**Total: 110 passed / 4 failed — the 4 failures are a single known infrastructure limitation, not
an application bug.**

## Known limitation (not a code bug) — S3 object storage unreachable in this sandbox

- **Symptom:** post thumbnail upload, profile picture upload, and their corresponding delete calls
  (which depend on an image having been set) fail with `500` / S3 `ClientError`.
- **Investigated:** DNS resolves and the TLS handshake to the configured Supabase S3-compatible
  endpoint succeeds, but every authenticated S3 API call (even a plain `ListObjectsV2`) returns a
  non-standard HTTP `540` with an empty body — checked both default (virtual-hosted-style) and
  forced path-style addressing, same result either way. This points to the Supabase project's
  storage service or credentials, not the application code: the request-building, auth flow, error
  handling, and the previously-fixed `/users/{userid}/picture` and `/posts/{id}/image` routing all
  work correctly right up to the point of calling S3, and the frontend correctly surfaces the
  failure as an error banner instead of crashing (verified in both E2E runs).
- **Action needed (outside this codebase):** verify the Supabase project's storage service is
  active and the `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY`/`S3_BUCKET_NAME` in `backend/.env` are
  current, then re-run the picture/thumbnail upload tests.

## Final endpoint/flow coverage

All items in [testing-plan.md](testing-plan.md)'s checklists were executed. Every one passed
except the S3-dependent upload/delete cases above.
