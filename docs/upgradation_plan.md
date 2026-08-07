# Upgrade Plan — FastAPI Blogger

Status: **all sections below complete and verified.** Status legend: `[ ]` not started ·
`[~]` in progress · `[x]` done.

## Why this plan exists

The user resumed the paused Supabase project and reported: forms with no visible submit buttons,
a very plain/basic UI, a profile page with no visible picture, and an empty app with nothing to
look at. This plan diagnoses root causes, then upgrades both the frontend UI and, where it
actually improves the product, the backend.

## 0. Root-cause diagnosis (done before writing the rest of this plan)

Screenshotted Login/Register/Home in a real headless browser. Finding: **every "invisible button"
report is the same bug.** `frontend/src/index.css` never actually defined the `--color-brand-*`
design tokens it was supposed to (a leftover from an earlier edit that silently failed and was
never re-added). Tailwind v4 drops unknown utility classes with no warning, so every
`bg-brand-600`, `text-brand-700`, `ring-brand-500`, `border-brand-*` class in the app — used on
every primary button, every link, every focus ring — compiled to nothing. Buttons exist and work
(confirmed via the E2E suite, which clicks them by selector, not by sight); they're just white text
on a white/transparent background. This is why the app "has no buttons" and "looks basic": the one
color that was supposed to carry all visual hierarchy was never actually shipped.

Secondary findings:
- The database is empty (0 posts/users) post-resume, so even a fixed UI has nothing to show.
- `UserProfile`/`Settings` render a broken-image icon (or, after an earlier fix, nothing at all)
  for any user without an uploaded picture — there's no placeholder avatar, so "no profile pic"
  looks broken rather than looking like a default state.
- Beyond the color bug, the visual design itself is minimal: no hero/intro on the home page, no
  visual hierarchy beyond font-size, no search, plain list-only empty states, nav has no mobile
  treatment.

## 1. Critical fix (P0)

- [x] Define the actual `--color-brand-*` scale in `frontend/src/index.css` `@theme` block
      (100/500/600/700, matching every shade already referenced across the codebase) so every
      existing `bg-brand-*`/`text-brand-*`/`ring-brand-*`/`border-brand-*` class starts rendering.
      Verified visually via screenshot after the fix.

## 2. Shared design system (new reusable components, P1)

Small, focused components so the rest of the redesign is consistent instead of one-off Tailwind
soup per page.

- [x] `Avatar` — renders the user's picture if `image_file` is set; otherwise a colored circle
      with their initials (color derived deterministically from user id, so the same user always
      gets the same color). Solves the "no profile pic" problem for every user who hasn't
      uploaded one, which by default is everyone.
- [x] `Button` — primary/secondary/danger/ghost variants, consistent sizing, used everywhere a
      raw `<button className="...">` was hand-rolled before.
- [x] `EmptyState` — icon + message + optional CTA, replacing bare "No posts yet." text.
- [x] `Skeleton` — pulse-loading placeholders for post cards, replacing the generic spinner on the
      feed/profile pages (spinner kept for auth-gated full-page loads).

## 3. Backend additions (only what the upgraded frontend actually needs, P1)

- [x] `GET /posts?search=<query>` — case-insensitive title/content match (SQL `ILIKE`), optional
      query param, backward compatible (omitting it behaves exactly as before). Powers a real
      search box on the home page.
- [x] `GET /admin/users` — paginated user list (id, username, email, is_admin, post count).
      The admin dashboard currently can only moderate a user if the admin already knows their
      numeric ID, which isn't how moderation works in practice. This is a straightforward
      read-only addition, no schema changes.

## 4. Frontend redesign, page by page (P1/P2)

- [x] `Layout` — sticky header, mobile hamburger menu, active-route highighting, avatar in nav
      instead of plain username text.
- [x] `Home` — hero intro section, search box (debounced, wired to the new `search` param),
      skeleton loading grid, richer empty state with a "write the first post" CTA for logged-in
      users.
- [x] `PostCard` — author avatar + name, better spacing/typography, hover elevation, graceful
      missing-thumbnail layout (no broken image gap).
- [x] `PostDetail` — author avatar in byline, refined comment thread visuals, `Avatar` in every
      comment/reply.
- [x] `PostForm` / `PostCreate` / `PostEdit` — visual pass using the new `Button` component,
      clearer section separation between "post content" and "thumbnail".
- [x] `UserProfile` — large `Avatar`, cleaner stat/action layout, admin actions visually separated.
- [x] `Settings` — `Avatar` preview wired to the real upload flow, sectioned cards instead of a
      flat stacked form.
- [x] `AdminDashboard` — replace the "type a user ID and hope" lookup with a real paginated user
      table (using the new `GET /admin/users`) with inline role-toggle/ban actions; keep metrics
      and top-posts sections, restyled to match.
- [x] `NotFound`, `Login`, `Register`, `ForgotPassword`, `ResetPassword` — visual pass with `Button`
      and consistent card layout.

## 5. Dummy seed data (P1)

- [x] `backend/seed.py` — idempotent-ish script (safe to re-run; skips if seed users already
      exist) that creates ~6 realistic dummy users and ~14 posts with real paragraph-length
      content across a few different "topics" (so the search feature has something to search),
      plus comments, replies, and likes scattered across them, so the app looks like a real,
      lived-in blog instead of an empty shell. Run once against the resumed Supabase database.

## 6. Verification

- [x] Re-screenshot every redesigned page after the fixes land.
- [x] Re-run the existing E2E suite (from the prior testing round) against the redesigned frontend
      to confirm no regressions in actual functionality, not just looks.
- [x] Update this file's checkboxes as each section completes.

Final numbers: 66 backend checks passed (57 core + 9 admin), 41 frontend browser checks passed
(27 core flows + 14 admin dashboard), 0 failures.

## 7. Additional bugs found while implementing this plan

Two of these only became visible once Supabase was resumed and image uploads started actually
reaching S3 for the first time — they were invisible in the previous testing round because every
upload attempt failed before reaching the code path that had the bug.

- **`image_path` produced a broken URL for every uploaded image.** `models.py` built public object
  URLs by appending `/storage/v1/object/public/<bucket>/<file>` onto
  `settings.s3_endpoint_url`, but that setting is already the S3-*protocol* endpoint
  (`.../storage/v1/s3`, used by `boto3`) — appending the public-URL path onto it produced a
  doubled, invalid path (`.../storage/v1/s3/storage/v1/object/public/...`). It was also missing
  the `profile_images/`/`post/` key prefix that uploads actually use. Both a real user's uploaded
  profile picture and every post thumbnail would have silently failed to display. Fixed with a
  shared `_public_object_url()` helper; verified an uploaded image's URL now resolves with
  `naturalWidth: 800` in a real browser.
- **Admin user list ordered oldest-first**, so newly registered users fell off the first page by
  default, which is backwards for a moderation tool (admins care about new signups). Changed to
  newest-first (`id.desc()`).

## 8. Known follow-ups (not blocking, not done)

- The admin dashboard's user table has no search/filter — for a platform with many users, an
  admin would need to page through to find someone by name. Pagination works; a search box would
  be a natural next step.
- No image cropping/preview-before-upload — files are uploaded immediately on selection and
  server-side cropped to a fixed aspect ratio. A client-side crop step would give users more
  control but wasn't in scope for this pass.
