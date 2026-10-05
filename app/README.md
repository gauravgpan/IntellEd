# ThinkTurf MVP — app skeleton

A thin, running skeleton across every Must-have module in
[`docs/mvp/technical-design.md`](../docs/mvp/technical-design.md): auth,
roles, the data model, and empty-but-wired endpoints/screens for each
module. Nothing here is feature-complete — see "What's not here yet" below.

Stack: LAMP + Python — Apache (prod) / Django + Django REST Framework / MySQL
/ React (Vite), with Django-Q2 for background/scheduled work (its ORM broker
runs off the same MySQL database — no Redis needed).

## Layout

```
app/
  backend/     Django project — one app per module (users, schools,
               students, curriculum, scheduling, submissions, assessments,
               reports)
  frontend/    React + Vite SPA (OTP login, dashboard, schedule, class view,
               student report, submission review, tutor onboarding)
  docker-compose.yml   Local dev only (MySQL + backend). Production serves
                       through Apache/mod_wsgi — see backend/apache/.
```

## Running it locally

**Backend**

```bash
cd app/backend
cp .env.example .env          # edit if needed
pip install -r requirements.txt
# Fastest path, no MySQL needed: set USE_SQLITE=1 in .env
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_schedules   # registers the reminder-dispatch job (idempotent)
python manage.py runserver
```

In a second terminal, start the Django-Q2 worker — without it, uploaded
submissions never leave "Uploaded" and reminders never send, since both
now run as background jobs rather than inline in a request:

```bash
cd app/backend
python manage.py qcluster
```

Or with Docker (MySQL + backend + the qcluster worker, all included):

```bash
cd app
docker compose up --build
# then once, in another terminal:
docker compose exec backend python manage.py setup_schedules
```

**Frontend**

```bash
cd app/frontend
npm install
npm run dev
```

The dev server proxies `/api` to `localhost:8000` (see `vite.config.js`), so
no CORS setup is needed locally.

## What's here

Every Must-have module from the design doc has a working vertical slice:
models, migrations-ready Django apps, DRF endpoints with role-based
permissions (Founder/Admin/Tutor), and matching React screens:

- OTP login (email or phone), token auth
- Tutor onboarding + lifecycle (Applied → Verified → Active →
  Suspended/Inactive), admin approval
- Schools, classes, tutor assignments (many-to-many)
- Students (pseudonymous token + separate PII table), subscriptions
- Curriculum: lessons, handouts, per-class lesson plan
- Scheduling: sessions, attendance, performance notes, and **system-triggered
  reminders** — scheduling or rescheduling a session registers its reminder
  (`Session.save()`), and a Django-Q2 job (`apps/scheduling/tasks.py`,
  `python manage.py setup_schedules`) checks every 15 minutes for ones due to
  send — design doc §5, §10 open decision 5
- **Class view**: strength, roster, handout progress (Done / In progress /
  To do), reachable from the schedule or by search — design doc §6
- Submissions: upload → review/confirm → or waive, design doc §7–§8
- Cognitive Skill Snapshot: consent-gated, cycle-numbered re-assessments
- Individual student report

The 10 open decisions in the design doc (§10) are resolved as explicit,
commented assumptions — grep `settings.py` and model/view docstrings for
`NOTE (open decision` and `settings.*` feature flags. Flip a setting or
re-read the comment once the team actually decides; nothing else needs to
change.

## What's not here yet

- **Extraction worker** (`apps/submissions/services.py`): the content is a
  stub — no OCR/vision model wired up — but the plumbing is real: it runs as
  a queued Django-Q2 task, not inline in the request. That's the seam where
  a real pipeline plugs in.
- **Reminder delivery** (`apps/scheduling/services.py.send_reminder`): same
  shape — the job that finds due reminders and calls this runs for real
  (every 15 minutes, via Django-Q2), it's the actual send (email/SMS/push)
  that's stubbed to a log line.
- **OTP delivery** (`apps/users/services.py`): logs the code instead of
  sending email/SMS. Swap in a real provider.
- Tests, CI, and the Good/May-have backlog (design doc §11) — deliberately
  deferred, same as the design doc.

## Open decisions baked in as assumptions

See `backend/config/settings.py` (bottom) and `NOTE` comments across
`models.py`/`views.py` in each app. Summary:

| # | Decision | Assumption used here |
|---|---|---|
| 1 | Tutor approval authority | Admin or Founder, either can approve |
| 2 | No rejection state for failed verification | Not modeled; easy to add `Tutor.LIFECYCLE_REJECTED` later |
| 3 | How guardian consent is evidenced | Not modeled beyond the outcome (`ConsentRecord`) |
| 4 | Extraction auto-commit | Never — tutor must confirm via `/submissions/{id}/confirm/` |
| 5 | Reminder recipients | Tutors only (no parent accounts) |
| 6 | School Onboarded → Active trigger | First session scheduled (`Session.save()`) |
| 7 | Lesson sequence owner | Admin/Founder only (`CLASS_PLAN_EDITABLE_BY_TUTOR = False`) |
| 8 | What counts as "submitted" | Confirmed + Waived (`SUBMISSION_STATUSES_COUNTED_AS_DONE`) |
| 9 | Mid-year roster changes | `Student.enrolled_at` recorded, not yet used to adjust the Done denominator |
| 10 | Who may waive | Any assigned tutor (`ANY_ASSIGNED_TUTOR_CAN_WAIVE = True`) |
