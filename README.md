# Fuzail Labs - AI Generated MVP Development in 24 Hours

Modern SaaS platform with AI MVP generation pipeline built using Flask, SQLAlchemy, Flask-Login, CSRF protection, and asynchronous background generation.

## Included pages
- Home (hero, pricing, features, how-it-works, portfolio, FAQ, testimonials)
- Order form (idea submission + AI generation trigger)
- Contact form
- Blog/news section
- User login/signup + user dashboard
- Admin login + admin dashboard

## AI MVP generator flow
1. User submits startup idea from order form.
2. Request is stored in DB.
3. Background worker starts AI generation (`Pending -> Generating`).
4. OpenAI is called to generate project files (fallback scaffold if unavailable).
5. Project folder and ZIP are created in `generated_projects/`.
6. User can download ZIP from dashboard.
7. Email notification is sent on completion (if mail is configured).

## Admin features
- View submitted project requests
- Update request status (`Pending`, `Generating`, `Completed`, `Delivered`)
- Approve/re-trigger project generation
- Download all generated project archives
- Export requests as CSV
- Optional status email notifications (if mail env vars are configured)

## Quick start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example` and set values.
3. Run:
   ```bash
   python app.py
   ```
4. Open: `http://127.0.0.1:5000`

## Default admin credentials
- Email: `admin@fuzaillabs.com`
- Password: `admin12345`

Change these using `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`.

## Deployment files
- `Dockerfile`
- `docker-compose.yml`
- `Procfile`
- `railway.json`
- `vercel.json`

## Runtime folders
- `generated_projects/` for generated project folders and ZIP files
- `logs/` for system logs
- `app/`, `routes/`, `models/`, `services/`, `utils/` placeholders for modular architecture
