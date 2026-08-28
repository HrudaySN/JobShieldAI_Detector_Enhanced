# JobShield AI — Flask project

Signup, login, Google Sign-In, password reset, an explainable job-risk
baseline model, and the responsive UI all work locally on SQLite.

## What's inside

```
app.py                  - app factory, run this
config.py                - reads settings from .env
extensions.py             - db / login_manager / mail instances
models.py                 - User model
forms.py                  - WTForms (also gives CSRF protection)
auth.py                    - signup/login/logout/google/password-reset routes
main.py                    - home page route
google_auth.py             - Google OAuth (Authlib) setup
templates/                 - your pages, converted to Jinja2
job_analyzer.py           - dependency-free Naive Bayes risk baseline
data/job_postings_sample.csv - labelled demo dataset used for training
static/css, static/js       - responsive stylesheets + interactions
```

## Setup

```bash
cd flask_project
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
- `SECRET_KEY` — any random string (used to sign sessions and reset tokens)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — see below
- Leave `MAIL_USERNAME` blank while developing — reset links will be printed
  to your terminal instead of emailed, so the flow still works.

Run it:

```bash
python app.py
```

Visit `http://127.0.0.1:5000/`.

## Setting up Google Sign-In

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Application type: **Web application**).
3. Under **Authorized redirect URIs**, add:
   `http://127.0.0.1:5000/google/callback`
   (and later your production URL, e.g. `https://yourdomain.com/google/callback`)
4. Copy the Client ID and Client Secret into `.env`.

That's it — the `/google/login` link on the login/signup pages will redirect
to Google, and `/google/callback` creates or logs in the matching user.

## How the pieces map to your Django templates

| Django template | Flask template | Route |
|---|---|---|
| `login.html` | `templates/login.html` | `GET/POST /login` |
| `signup.html` | `templates/signup.html` | `GET/POST /signup` |
| `signup.html` ("Almost done" username step) | `templates/signup_username.html` | `GET/POST /username` |
| `home.html` | `templates/home.html` | `GET /` |
| `password_reset.html` | `templates/password_reset.html` | `GET/POST /password-reset` |
| `password_reset_done.html` | `templates/password_reset_done.html` | `GET /password-reset/done` |
| `password_reset_from_key.html` | `templates/password_reset_from_key.html` | `GET/POST /password-reset/<token>` |
| `password_reset_from_key_done.html` | `templates/password_reset_from_key_done.html` | `GET /password-reset/complete` |

## Bugs I fixed while converting

- **`home.html` was broken**: it ended with `{{ block.super|default:"" }}` and
  a comment saying "keep everything below the same as your teammate's file" —
  that's leftover Django template-inheritance syntax with nothing to inherit
  from, so the page would render a blank/broken bottom half. I rebuilt it as
  one self-contained page with real section content instead.
- **Dead nav links**: `Detect Job`, `About`, `Safety Hub`, `Contact`, and
  `Get Started` all pointed at `href="#"` or nowhere. They now point at
  in-page anchors (`#detect`, `#about`, etc.) so the nav actually scrolls
  somewhere — swap these for real routes once those pages exist.
- **Two duplicate signup templates**: your upload had `signup.html` (using
  Django's form-rendering with granular per-field errors) and a second,
  simpler `signup.html` with raw `<input>` tags and no CSRF token or
  validation. I merged them: kept the granular error handling, used WTForms
  fields (adds CSRF protection, which the plain-input version was missing
  entirely), and folded the username step in as its own page/route rather
  than cramming it into signup.
- **Password reset used to be all-or-nothing**: your `password_reset_from_key.html`
  had a `token_fail` branch but nothing in the Django views was shown to
  produce it. Wired that up properly with `itsdangerous` timed tokens
  (1 hour expiry, configurable in `config.py`).

## Fake-job risk model

`POST /api/analyze-job` runs a small multinomial Naive Bayes baseline trained
from `data/job_postings_sample.csv`. It also highlights high-priority signals
such as a request for payment or bank details. Results are deliberately shown
as a **risk score**, not a guarantee: a user should always verify a company
independently before sharing information or money.

For the project review, this gives you a useful demonstration path:

1. Open **Detector** and paste a job post.
2. The score, specific matched signals, model name, and dataset size appear.
3. Show the CSV dataset and explain that it can grow through curated labelled
   examples; retraining happens on application startup.

## Notes / things you'll want to decide on

- **Database**: SQLite by default (zero setup). Point `DATABASE_URL` at
  Postgres/MySQL later without touching any code.
- **Sending real emails**: fill in `MAIL_USERNAME`/`MAIL_PASSWORD` in `.env`
  (a Gmail "app password" works well) once you're ready — until then reset
  links just print to the console.
- **Resume screening** currently uses a UI demonstration result. A next
  backend step would be text extraction from PDF/DOCX followed by a similar
  explainable skills-matching model.
