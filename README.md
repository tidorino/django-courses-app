# Django + Tailwind CSS + PostgreSQL Boilerplate

A minimal, working starting point:

- **Backend**: Django (project `config`, starter app `core`)
- **Frontend**: Tailwind CSS (compiled via the Tailwind CLI, no runtime JS framework)
- **Database**: PostgreSQL, configured via `DATABASE_URL` (falls back to local SQLite if unset, so it runs out of the box)

```
.
├── config/              # Django project (settings, urls, wsgi/asgi)
├── core/                # Starter app — put your models/views/urls here first
├── templates/           # base.html + page templates
├── static_src/styles.css  # Tailwind source file
├── static/css/styles.css  # Compiled Tailwind output (generated, gitignored)
├── requirements.txt
├── package.json         # Tailwind CLI build scripts
├── Dockerfile / docker-compose.yml
└── .env.example
```

## Option A — Run with Docker (recommended, includes Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Then in another terminal, run migrations the first time:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Visit **http://localhost:8000**. Django admin is at **/admin/**.

If you edit Tailwind classes, the CSS in the image won't hot-reload — rebuild with:

```bash
docker compose up --build web
```

(For active frontend work, Option B's `npm run dev` watch mode is faster.)

## Option B — Run locally (Python + Node, Postgres running separately)

1. **Python environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env`. If you have Postgres running locally, create a database and user, then set:

   ```
   DATABASE_URL=postgres://appuser:apppassword@localhost:5432/appdb
   ```

   If you skip this, the app automatically uses a local `db.sqlite3` file — useful for
   just poking around before Postgres is set up.

3. **Tailwind CSS**

   ```bash
   npm install
   npm run build     # one-off build
   # or, while developing:
   npm run dev        # watches templates and rebuilds on change
   ```

4. **Django**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

Visit **http://localhost:8000**.

## Creating a Postgres database locally (if not using Docker)

```bash
psql postgres
CREATE DATABASE appdb;
CREATE USER appuser WITH PASSWORD 'apppassword';
GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;
```

## What's already wired up

- `core` — landing page
- `accounts` — signup (student or instructor role), login, logout
- `courses` — the online courses feature (see below)
- Env-based settings (`django-environ`) — nothing sensitive is hardcoded
- Whitenoise for serving static files (works the same in dev and in Docker/production)
- `.gitignore` covering Python, Django, Node and env files

## The courses app

**Models** (`courses/models.py`):
- `Category` — optional grouping for courses
- `Course` — title, description, price, cover image, instructor (a `User`), published/draft
- `Module` — a named section within a course (e.g. "Getting Started")
- `Lesson` — belongs to a module; has text content, an optional video URL (YouTube links are
  auto-converted to embeds; direct `.mp4` URLs work too via an HTML5 `<video>` tag), and an
  `is_preview` flag for free-preview lessons
- `Enrollment` — links a `User` to a `Course` they have access to

**Roles**: every user has a `Profile` (`accounts/models.py`) with `is_instructor`. Set at
signup. Instructors get a dashboard at `/courses/instructor/` to create courses and manage
modules/lessons. Everyone else just browses and enrolls.

**Progress tracking**: each `Lesson` a user marks complete creates a `LessonProgress` row
(`courses/models.py`). `Course.progress_percent(user)` computes completed/total lessons.
Students see a progress bar on the course page, on each lesson page, and a per-course
percentage on "My Courses". Lesson pages also have Previous/Next navigation and a
"Mark as complete" toggle.

**Payment status — read this**: Enrollment is currently a placeholder. Clicking "Enroll now"
on a paid course immediately creates a `completed` Enrollment with no real charge — there's no
payment gateway wired up yet. This was intentional so the whole flow (browsing → lesson
access control → dashboards) works today. When you're ready to add real payments (e.g.
Stripe Checkout), the natural place to plug it in is `courses/views.py::enroll`:
create the `Enrollment` as `"pending"`, redirect to the payment provider's checkout,
then flip it to `"completed"` in a webhook/return view instead of doing it inline.

**Access control**: a lesson's content is visible if the lesson is marked `is_preview=True`,
or the logged-in user has a `completed` Enrollment for that course, or the user is the
course's instructor. Everything else redirects back to the course page with a message
prompting the user to enroll.

## Trying it out locally

1. Follow the setup steps above (Docker or local) and get to a running server.
2. Sign up at `/accounts/signup/` and choose **Instructor**.
3. Go to `/courses/instructor/`, create a course, add a module, add a lesson or two
   (mark one as a free preview).
4. Edit the course and check "Published".
5. Open an incognito window (or log out), sign up as a **Student**, browse to the course
   at `/courses/`, and enroll.

## Next steps to consider

- Real payments (Stripe Checkout is the natural fit — see the note above)
- Course search/filtering by category
- Reviews/ratings on courses
