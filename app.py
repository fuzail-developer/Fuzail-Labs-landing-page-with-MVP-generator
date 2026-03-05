from __future__ import annotations

import csv
import io
import logging
import os
import re
import shutil
import threading
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT_DIR / "generated_projects"
LOGS_DIR = ROOT_DIR / "logs"
AI_SAVE_PREFIX = "ACTION:save_file:"
LANDING_PAGE_KEYWORDS = (
    "landing page",
    "marketing",
    "saas website",
    "pricing page",
    "order form",
    "portfolio",
    "testimonial",
    "faq",
    "blog section",
)
ALLOWED_STATUSES = {"Pending", "Generating", "Completed", "Delivered"}
ALLOWED_FRAMEWORKS = {"Flask", "FastAPI", "Django"}
ALLOWED_DATABASES = {"SQLite", "PostgreSQL", "MySQL", "Supabase"}
ALLOWED_PLANS = {"Basic MVP", "Startup MVP", "Full SaaS", "Not sure yet"}


def _normalize_database_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql://", 1)
    return value or "sqlite:///fuzail_labs.db"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug[:50] or "saas-mvp"


def _ensure_runtime_dirs() -> None:
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    for folder in ("app", "routes", "models", "services", "templates", "static", "utils"):
        (ROOT_DIR / folder).mkdir(parents=True, exist_ok=True)


_ensure_runtime_dirs()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / "system.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("fuzail-labs")

app = Flask(__name__, template_folder="templates")
secret_key = os.getenv("SECRET_KEY", "").strip()
if not secret_key:
    raise RuntimeError("SECRET_KEY is required. Set it in .env or environment.")

app.config["SECRET_KEY"] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///fuzail_labs.db"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", app.config["MAIL_USERNAME"])
app.config["ORDER_ALERT_EMAIL"] = os.getenv("ORDER_ALERT_EMAIL", "fuzailshaik42@gmail.com").strip()
app.config["FOUNDER_NAME"] = os.getenv("FOUNDER_NAME", "Fuzail")
app.config["FOUNDER_LINKEDIN_URL"] = os.getenv("FOUNDER_LINKEDIN_URL", "").strip()
app.config["FOUNDER_GITHUB_URL"] = os.getenv("FOUNDER_GITHUB_URL", "https://github.com/fuzail-developer").strip()
app.config["BUILT_MVPS_COUNT"] = os.getenv("BUILT_MVPS_COUNT", "").strip()
app.config["DEMO_1_TITLE"] = os.getenv("DEMO_1_TITLE", "60SecAI (Instant Life Fix Coach)").strip()
app.config["DEMO_1_URL"] = os.getenv("DEMO_1_URL", "https://six0secai-ai-wellness-app-1.onrender.com").strip()
app.config["DEMO_1_GITHUB_URL"] = os.getenv(
    "DEMO_1_GITHUB_URL",
    "https://github.com/fuzail-developer/60secai-ai-wellness-app",
).strip()
app.config["DEMO_1_DESC"] = os.getenv(
    "DEMO_1_DESC",
    "GitHub: https://github.com/fuzail-developer/60secai-ai-wellness-app",
).strip()
app.config["DEMO_2_TITLE"] = os.getenv("DEMO_2_TITLE", "AI CRM Flask (Full-Stack CRM)").strip()
app.config["DEMO_2_URL"] = os.getenv("DEMO_2_URL", "https://ai-crm-flask.onrender.com").strip()
app.config["DEMO_2_GITHUB_URL"] = os.getenv(
    "DEMO_2_GITHUB_URL",
    "https://github.com/fuzail-developer/ai-CRM-flask",
).strip()
app.config["DEMO_2_DESC"] = os.getenv(
    "DEMO_2_DESC",
    "GitHub: https://github.com/fuzail-developer/ai-CRM-flask",
).strip()
app.config["SCOPE_CALL_URL"] = os.getenv("SCOPE_CALL_URL", "").strip()
app.config["CONTACT_EMAIL"] = os.getenv("CONTACT_EMAIL", "fuzailshaik42@gmail.com").strip()
app.config["CONTACT_PHONE"] = os.getenv("CONTACT_PHONE", "7454099494").strip()
app.config["CONTACT_ADDRESS"] = os.getenv(
    "CONTACT_ADDRESS",
    "Muzaffarnagar, Uttar Pradesh, India",
).strip()
app.config["LAUNCH_YEAR"] = os.getenv("LAUNCH_YEAR", "2025").strip()
app.config["TESTIMONIAL_1_QUOTE"] = os.getenv("TESTIMONIAL_1_QUOTE", "").strip()
app.config["TESTIMONIAL_1_NAME"] = os.getenv("TESTIMONIAL_1_NAME", "").strip()
app.config["TESTIMONIAL_1_ROLE"] = os.getenv("TESTIMONIAL_1_ROLE", "").strip()
app.config["TESTIMONIAL_2_QUOTE"] = os.getenv("TESTIMONIAL_2_QUOTE", "").strip()
app.config["TESTIMONIAL_2_NAME"] = os.getenv("TESTIMONIAL_2_NAME", "").strip()
app.config["TESTIMONIAL_2_ROLE"] = os.getenv("TESTIMONIAL_2_ROLE", "").strip()

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

_openai_client: Optional[Any] = None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    requests = db.relationship("ProjectRequest", backref="owner", lazy=True, cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class ProjectRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    idea = db.Column(db.Text, nullable=False)
    framework = db.Column(db.String(32), nullable=False)
    database = db.Column(db.String(32), nullable=False)
    plan = db.Column(db.String(32), nullable=False)
    package = db.Column(db.String(50), nullable=True)
    extra = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="Pending")
    generated_folder = db.Column(db.String(255), nullable=True)
    zip_filename = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    messages = db.relationship(
        "RequestMessage",
        backref="request",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="RequestMessage.created_at.asc()",
    )


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class RequestMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("project_request.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False, default="customer")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return User.query.get(int(user_id))


def _require_admin() -> None:
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        abort(403)


def _mail_is_configured() -> bool:
    server = str(app.config.get("MAIL_SERVER", "")).strip().lower()
    sender = str(app.config.get("MAIL_DEFAULT_SENDER", "")).strip().lower()
    user = str(app.config.get("MAIL_USERNAME", "")).strip().lower()
    password = str(app.config.get("MAIL_PASSWORD", "")).strip()
    if not all([server, sender, user, password]):
        return False
    placeholders = ("example.com", "your-email", "changeme")
    if any(p in sender for p in placeholders):
        return False
    if any(p in user for p in placeholders):
        return False
    if any(p in password.lower() for p in placeholders):
        return False
    return True


@app.context_processor
def inject_brand_context() -> Dict[str, Any]:
    testimonials = []
    q1 = app.config.get("TESTIMONIAL_1_QUOTE", "")
    n1 = app.config.get("TESTIMONIAL_1_NAME", "")
    r1 = app.config.get("TESTIMONIAL_1_ROLE", "")
    if q1 and n1:
        testimonials.append({"quote": q1, "name": n1, "role": r1})
    q2 = app.config.get("TESTIMONIAL_2_QUOTE", "")
    n2 = app.config.get("TESTIMONIAL_2_NAME", "")
    r2 = app.config.get("TESTIMONIAL_2_ROLE", "")
    if q2 and n2:
        testimonials.append({"quote": q2, "name": n2, "role": r2})

    return {
        "founder_name": app.config.get("FOUNDER_NAME", "Founder"),
        "founder_linkedin_url": app.config.get("FOUNDER_LINKEDIN_URL", ""),
        "founder_github_url": app.config.get("FOUNDER_GITHUB_URL", ""),
        "built_mvps_count": app.config.get("BUILT_MVPS_COUNT", ""),
        "demo_1_title": app.config.get("DEMO_1_TITLE", "Demo Project 1"),
        "demo_1_url": app.config.get("DEMO_1_URL", ""),
        "demo_1_github_url": app.config.get("DEMO_1_GITHUB_URL", ""),
        "demo_1_desc": app.config.get("DEMO_1_DESC", ""),
        "demo_2_title": app.config.get("DEMO_2_TITLE", "Demo Project 2"),
        "demo_2_url": app.config.get("DEMO_2_URL", ""),
        "demo_2_github_url": app.config.get("DEMO_2_GITHUB_URL", ""),
        "demo_2_desc": app.config.get("DEMO_2_DESC", ""),
        "scope_call_url": app.config.get("SCOPE_CALL_URL", ""),
        "contact_email": app.config.get("CONTACT_EMAIL", "fuzailshaik42@gmail.com"),
        "contact_phone": app.config.get("CONTACT_PHONE", ""),
        "contact_address": app.config.get("CONTACT_ADDRESS", ""),
        "launch_year": app.config.get("LAUNCH_YEAR", "2025"),
        "current_year": str(datetime.utcnow().year),
        "testimonials": testimonials,
    }


def _send_status_email(req: ProjectRequest, completed: bool = False) -> None:
    if not _mail_is_configured():
        logger.info("Mail not configured. Request=%s Status=%s", req.id, req.status)
        return
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    download_link = f"{base_url}/project/{req.id}/download"
    subject = f"Fuzail Labs Project Update: {req.status}"
    body = (
        f"Hi {req.name},\n\n"
        f"Your request #{req.id} is now: {req.status}\n"
        f"Framework: {req.framework}\nDatabase: {req.database}\nPlan: {req.plan}\n"
    )
    if completed and req.zip_filename:
        body += f"\nYour MVP is ready. Download here:\n{download_link}\n"
    body += "\nThanks,\nFuzail Labs"
    try:
        msg = Message(subject=subject, recipients=[req.email], body=body)
        mail.send(msg)
    except Exception as exc:
        logger.warning("Status email failed for request %s: %s", req.id, exc)


def _send_new_order_alert(req: ProjectRequest) -> None:
    target = str(app.config.get("ORDER_ALERT_EMAIL", "")).strip()
    if not target:
        logger.info("ORDER_ALERT_EMAIL not configured. Skipping alert for request=%s", req.id)
        return
    if not _mail_is_configured():
        logger.info("Mail not configured. New-order alert skipped for request=%s", req.id)
        return

    subject = f"New MVP Order #{req.id} from {req.email} - {req.plan}"
    body = (
        "A new MVP order has been submitted.\n\n"
        f"Request ID: {req.id}\n"
        f"Name: {req.name}\n"
        f"Email: {req.email}\n"
        f"Phone: {req.phone or '-'}\n"
        f"Plan: {req.plan}\n"
        f"Framework: {req.framework}\n"
        f"Database: {req.database}\n"
        f"Idea: {req.idea}\n"
        f"Extra: {req.extra or '-'}\n"
        f"Created: {req.created_at.isoformat()}\n"
    )
    try:
        msg = Message(
            subject=subject,
            recipients=[target],
            body=body,
            reply_to=req.email,
        )
        mail.send(msg)
    except Exception as exc:
        logger.warning("New-order alert failed for request %s: %s", req.id, exc)


def _ensure_admin() -> None:
    admin_email = (os.getenv("ADMIN_EMAIL") or "admin@fuzaillabs.com").strip().lower()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "admin12345").strip()
    admin_name = (os.getenv("ADMIN_NAME") or "Admin").strip()
    admin_username = (os.getenv("ADMIN_USERNAME") or "admin").strip()
    admin = User.query.filter_by(email=admin_email).first()
    if admin is None:
        hashed = generate_password_hash(admin_password)
        admin = User(
            username=admin_username[:120],
            name=admin_name[:120],
            email=admin_email[:120],
            password=hashed,
            password_hash=hashed,
            is_verified=True,
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        logger.info("Default admin user created: %s", admin_email)
    elif not getattr(admin, "username", None):
        admin.username = admin_username[:120]
        if not getattr(admin, "password", None):
            admin.password = admin.password_hash
        db.session.commit()


def _add_column_if_missing(table: str, column: str, ddl_sql: str) -> None:
    inspector = inspect(db.engine)
    if not inspector.has_table(table):
        return
    cols = {c["name"] for c in inspector.get_columns(table)}
    if column in cols:
        return
    logger.warning("Applying startup migration: add %s.%s", table, column)
    db.session.execute(text(ddl_sql))
    db.session.commit()


def _run_startup_migrations() -> None:
    # Lightweight SQLite-safe migrations for previously generated schemas.
    _add_column_if_missing(
        "user",
        "username",
        "ALTER TABLE user ADD COLUMN username VARCHAR(120) NOT NULL DEFAULT 'user'",
    )
    _add_column_if_missing("user", "name", "ALTER TABLE user ADD COLUMN name VARCHAR(120) NOT NULL DEFAULT 'User'")
    _add_column_if_missing(
        "user",
        "password",
        "ALTER TABLE user ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        "user",
        "password_hash",
        "ALTER TABLE user ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        "user",
        "is_verified",
        "ALTER TABLE user ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT 1",
    )
    _add_column_if_missing("user", "role", "ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
    _add_column_if_missing(
        "user",
        "created_at",
        "ALTER TABLE user ADD COLUMN created_at DATETIME",
    )
    _add_column_if_missing(
        "project_request",
        "user_id",
        "ALTER TABLE project_request ADD COLUMN user_id INTEGER",
    )
    _add_column_if_missing(
        "project_request",
        "generated_folder",
        "ALTER TABLE project_request ADD COLUMN generated_folder VARCHAR(255)",
    )
    _add_column_if_missing(
        "project_request",
        "zip_filename",
        "ALTER TABLE project_request ADD COLUMN zip_filename VARCHAR(255)",
    )
    _add_column_if_missing(
        "project_request",
        "error_message",
        "ALTER TABLE project_request ADD COLUMN error_message TEXT",
    )
    _add_column_if_missing(
        "project_request",
        "updated_at",
        "ALTER TABLE project_request ADD COLUMN updated_at DATETIME",
    )
    _add_column_if_missing(
        "project_request",
        "created_at",
        "ALTER TABLE project_request ADD COLUMN created_at DATETIME",
    )
    _add_column_if_missing(
        "project_request",
        "phone",
        "ALTER TABLE project_request ADD COLUMN phone VARCHAR(50)",
    )
    _add_column_if_missing(
        "project_request",
        "package",
        "ALTER TABLE project_request ADD COLUMN package VARCHAR(50)",
    )
    _add_column_if_missing(
        "project_request",
        "extra",
        "ALTER TABLE project_request ADD COLUMN extra TEXT",
    )

    inspector = inspect(db.engine)
    if inspector.has_table("user"):
        user_cols = {c["name"] for c in inspector.get_columns("user")}
        if "username" in user_cols and "email" in user_cols:
            db.session.execute(
                text(
                    "UPDATE user "
                    "SET username = CASE "
                    "WHEN email IS NOT NULL AND email <> '' THEN substr(email, 1, instr(email, '@') - 1) "
                    "ELSE 'user' || id END "
                    "WHERE username IS NULL OR username = ''"
                )
            )
            db.session.commit()
        if "password" in user_cols and "password_hash" in user_cols:
            db.session.execute(
                text(
                    "UPDATE user "
                    "SET password = password_hash "
                    "WHERE (password IS NULL OR password = '') "
                    "AND password_hash IS NOT NULL AND password_hash <> ''"
                )
            )
            db.session.commit()
            db.session.execute(
                text(
                    "UPDATE user "
                    "SET password_hash = password "
                    "WHERE (password_hash IS NULL OR password_hash = '') "
                    "AND password IS NOT NULL AND password <> ''"
                )
            )
            db.session.commit()
        if "is_verified" in user_cols:
            db.session.execute(
                text(
                    "UPDATE user "
                    "SET is_verified = 1 "
                    "WHERE is_verified IS NULL"
                )
            )
            db.session.commit()

    # Backfill null user_id rows to first admin/user where possible.
    if inspector.has_table("project_request") and inspector.has_table("user"):
        row = db.session.execute(text("SELECT id FROM user ORDER BY id ASC LIMIT 1")).fetchone()
        if row and row[0]:
            db.session.execute(
                text(
                    "UPDATE project_request "
                    "SET user_id = :uid "
                    "WHERE user_id IS NULL"
                ),
                {"uid": int(row[0])},
            )
            db.session.commit()
    if inspector.has_table("project_request"):
        req_cols = {c["name"] for c in inspector.get_columns("project_request")}
        if "plan" in req_cols and "package" in req_cols:
            db.session.execute(
                text(
                    "UPDATE project_request "
                    "SET package = plan "
                    "WHERE (package IS NULL OR package = '') "
                    "AND plan IS NOT NULL AND plan <> ''"
                )
            )
            db.session.commit()


def _openai_client_or_none() -> Optional[Any]:
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        _openai_client = OpenAI()
    except Exception as exc:
        logger.warning("OpenAI client initialization failed: %s", exc)
        return None
    return _openai_client


def _verify_user_password(user: User, raw_password: str) -> bool:
    stored_hash = (getattr(user, "password_hash", "") or "").strip()
    if stored_hash:
        try:
            return check_password_hash(stored_hash, raw_password)
        except Exception:
            pass
    legacy_value = (getattr(user, "password", "") or "").strip()
    if not legacy_value:
        return False
    try:
        return check_password_hash(legacy_value, raw_password)
    except Exception:
        return legacy_value == raw_password


def _parse_action_blocks(text: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    if AI_SAVE_PREFIX not in text:
        return files
    chunks = text.split(AI_SAVE_PREFIX)[1:]
    for chunk in chunks:
        sep = chunk.find(":")
        if sep == -1:
            continue
        path = chunk[:sep].strip().replace("\x00", "")
        body = chunk[sep + 1 :].strip()
        if AI_SAVE_PREFIX in body:
            body = body.split(AI_SAVE_PREFIX, 1)[0].strip()
        body = body.replace("```python", "").replace("```html", "").replace("```css", "").replace("```js", "").replace("```", "")
        if path and body:
            files[path] = body.strip()
    return files


def _is_landing_request(text: str) -> bool:
    idea = (text or "").strip().lower()
    return any(keyword in idea for keyword in LANDING_PAGE_KEYWORDS)


def _has_minimum_security_features(app_source: str, user_query: str) -> bool:
    landing_page_indicators = [
        "/order",
        "/contact",
        "/admin",
        "/pricing",
        "Order",
        "pricing",
        "landing",
        "landing_page",
    ]
    if _is_landing_request(user_query) or any(indicator in app_source for indicator in landing_page_indicators):
        return True

    required_markers = [
        "/forgot-password",
        "/reset-password/",
        "/verify-email/",
        "/project/export.zip",
        "is_verified",
    ]
    return all(marker in app_source for marker in required_markers)


def _fallback_scaffold(req: ProjectRequest) -> Dict[str, str]:
    framework = req.framework.lower()
    name = _slugify(req.idea)
    if framework == "fastapi":
        entry = (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI(title='Generated MVP')\n\n"
            "@app.get('/')\n"
            "def home():\n"
            "    return {'message': 'FastAPI MVP generated'}\n"
        )
        run_note = "Run: uvicorn main:app --reload"
        files = {
            "main.py": entry,
            "models.py": "from pydantic import BaseModel\n\nclass Item(BaseModel):\n    title: str\n",
            "routes.py": "from fastapi import APIRouter\nrouter = APIRouter()\n",
        }
    elif framework == "django":
        files = {
            "manage.py": (
                "#!/usr/bin/env python\n"
                "import os, sys\n"
                "if __name__ == '__main__':\n"
                "    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')\n"
                "    from django.core.management import execute_from_command_line\n"
                "    execute_from_command_line(sys.argv)\n"
            ),
            "project/settings.py": (
                "SECRET_KEY='change-me'\nDEBUG=True\nALLOWED_HOSTS=['*']\n"
                "INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',"
                "'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles']\n"
                "ROOT_URLCONF='project.urls'\n"
                "DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':'db.sqlite3'}}\n"
            ),
            "project/urls.py": "from django.urls import path\nfrom django.http import HttpResponse\nurlpatterns=[path('', lambda r: HttpResponse('Django MVP generated'))]\n",
            "models.py": "from django.db import models\n\nclass Item(models.Model):\n    title = models.CharField(max_length=120)\n",
            "routes.py": "# Define Django views in app modules.\n",
        }
        run_note = "Run: python manage.py runserver"
    else:
        files = {
            "app.py": (
                "from flask import Flask, render_template, request, redirect, url_for\n"
                "from flask_sqlalchemy import SQLAlchemy\n"
                "from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required\n\n"
                "app = Flask(__name__)\n"
                "app.config['SECRET_KEY'] = 'change-me'\n"
                "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'\n"
                "db = SQLAlchemy(app)\n"
                "login_manager = LoginManager(app)\n\n"
                "class User(UserMixin, db.Model):\n"
                "    id = db.Column(db.Integer, primary_key=True)\n"
                "    email = db.Column(db.String(120), unique=True)\n"
                "    password = db.Column(db.String(255))\n\n"
                "class Item(db.Model):\n"
                "    id = db.Column(db.Integer, primary_key=True)\n"
                "    title = db.Column(db.String(120), nullable=False)\n\n"
                "@app.route('/')\n"
                "def home():\n"
                "    return render_template('dashboard.html')\n\n"
                "if __name__ == '__main__':\n"
                "    with app.app_context():\n"
                "        db.create_all()\n"
                "    app.run(debug=True)\n"
            ),
            "models.py": "from flask_sqlalchemy import SQLAlchemy\ndb = SQLAlchemy()\n",
            "routes.py": "from flask import Blueprint\nbp = Blueprint('main', __name__)\n",
        }
        run_note = "Run: python app.py"

    files.update(
        {
            "requirements.txt": (
                "flask>=3.0.0\nflask-login>=0.6.3\nflask-sqlalchemy>=3.1.0\n"
                "python-dotenv>=1.0.0\nopenai>=2.0.0\n"
            ),
            "README.md": (
                f"# {name}\n\nGenerated by Fuzail Labs AI MVP Generator.\n\n"
                f"Framework: {req.framework}\nDatabase: {req.database}\nPlan: {req.plan}\n\n{run_note}\n"
            ),
            ".env.example": "SECRET_KEY=change-me\nDATABASE_URL=sqlite:///app.db\n",
            "templates/dashboard.html": "<h1>Generated Dashboard</h1>\n<p>Your MVP scaffold is ready.</p>\n",
            "templates/login.html": "<h1>Login</h1>\n<form method='post'><input name='email'><button>Login</button></form>\n",
            "templates/register.html": "<h1>Register</h1>\n<form method='post'><input name='email'><button>Register</button></form>\n",
            "static/style.css": "body{font-family:Arial,sans-serif;padding:2rem;}\n",
            "database_config.py": f"DATABASE='{req.database}'\n",
        }
    )
    return files


def _build_ai_prompt(req: ProjectRequest) -> str:
    is_landing_page = _is_landing_request(req.idea)
    if is_landing_page:
        extra_instructions = f"""
SPECIAL: This is a SaaS LANDING PAGE / MARKETING WEBSITE. Requirements:
- Home page with hero section, pricing, features, how it works, testimonials, FAQ
- /order page with project submission form
- /contact page with contact form
- /admin route with secure admin login (separate admin password from .env)
- Admin dashboard: view orders, update status (Pending/In Progress/Delivered), export CSV
- Order model: name, email, idea, framework, database, plan, status, created_at
- Contact model: name, email, message, created_at
- Blog model: title, slug, content, published_at (simple)
- Dark/light theme toggle
- SEO meta tags on every page
- Modern gradient hero (CSS only, no external images needed)
- Google Analytics placeholder in base template
- Footer with social links
- Visual direction must be bold and premium (not generic bootstrap look)
- Use a cinematic dark background with gradient + subtle scanline overlay
- Use a modern design token system with CSS variables for brand/accent/muted/border
- Cards should use glassmorphism, soft border glow, and hover lift transitions
- Buttons should use high-contrast gradient styles with hover glow and scale effects
- Include smooth reveal animation for sections/cards (staggered where possible)
- Typography should feel premium and intentional (large heading contrast + compact labels)
- Mobile responsive layout must be polished for 360px+ devices

Do NOT generate a generic app. Generate specifically for: {req.idea}
"""
        must_include = """
Must include:
- Landing home page (hero/features/pricing/testimonials/FAQ)
- /order page + order persistence
- /contact page + contact persistence
- /admin login + admin dashboard + CSV export
- requirements.txt
- README.md
- templates and static assets
"""
    else:
        extra_instructions = ""
        must_include = """
Must include:
- Login/Register
- Dashboard
- CRUD module
- Database models
- requirements.txt
- README.md
- templates and static assets
"""

    return f"""
You are a senior full-stack engineer. Generate a complete working SaaS MVP scaffold.
User idea: {req.idea}
Preferred framework: {req.framework}
Database: {req.database}
Plan: {req.plan}
{extra_instructions}

Return ONLY ACTION:save_file blocks in this format:
ACTION:save_file:path/to/file.ext:
<full file content>

{must_include}

Project tree target:
/project_name
  app.py or main.py
  requirements.txt
  models.py
  routes.py
  templates/
  static/
  README.md
"""


def _ensure_generated_project_integrity(files_map: Dict[str, str], req: ProjectRequest) -> Dict[str, str]:
    base = dict(files_map)
    fallback = _fallback_scaffold(req)
    is_landing = _is_landing_request(req.idea)

    framework = (req.framework or "flask").strip().lower()
    entry_file = "app.py"
    if framework == "fastapi":
        entry_file = "main.py"
    elif framework == "django":
        entry_file = "manage.py"

    if is_landing:
        required = [entry_file, "requirements.txt", ".env.example", "README.md"]
    else:
        required = [entry_file, "requirements.txt", ".env.example", "README.md"]
        if framework == "flask":
            required.extend(
                [
                    "templates/dashboard.html",
                    "templates/login.html",
                    "templates/register.html",
                ]
            )

    for path in required:
        if path not in base or not str(base[path]).strip():
            if path in fallback:
                base[path] = fallback[path]

    if framework == "flask" and entry_file in base:
        app_source = str(base[entry_file])
        if not _has_minimum_security_features(app_source, req.idea):
            logger.warning(
                "Generated app for request %s missed security markers; using fallback app.py",
                req.id,
            )
            base[entry_file] = fallback.get(entry_file, app_source)

    return base


def _generate_project_files(req: ProjectRequest) -> Dict[str, str]:
    client = _openai_client_or_none()
    if client is None:
        logger.info("OpenAI unavailable. Using fallback scaffold for request %s", req.id)
        return _fallback_scaffold(req)
    try:
        logger.info("AI generation started for request %s", req.id)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            max_tokens=7000,
            messages=[
                {"role": "system", "content": "Return only ACTION:save_file blocks."},
                {"role": "user", "content": _build_ai_prompt(req)},
            ],
        )
        text = (response.choices[0].message.content or "") if getattr(response, "choices", None) else ""
        files = _parse_action_blocks(text)
        if files:
            return _ensure_generated_project_integrity(files, req)
        logger.warning("AI returned no files for request %s. Using fallback.", req.id)
        return _fallback_scaffold(req)
    except Exception as exc:
        logger.warning("AI generation failed for request %s: %s", req.id, exc)
        return _fallback_scaffold(req)


def _save_generated_files(project_dir: Path, files: Dict[str, str]) -> None:
    base = project_dir.resolve()
    for rel_path, content in files.items():
        normalized = os.path.normpath(rel_path)
        if os.path.isabs(normalized):
            continue
        target = (base / normalized).resolve()
        try:
            if os.path.commonpath([str(base), str(target)]) != str(base):
                continue
        except ValueError:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _zip_project_folder(project_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(project_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, arcname=str(file_path.relative_to(project_dir)))


def _generation_worker(request_id: int) -> None:
    with app.app_context():
        req = ProjectRequest.query.get(request_id)
        if req is None:
            return
        req.status = "Generating"
        req.error_message = None
        db.session.commit()

        try:
            files = _generate_project_files(req)
            folder_name = f"{_slugify(req.idea)}-{req.id}"
            project_dir = GENERATED_ROOT / folder_name
            if project_dir.exists():
                shutil.rmtree(project_dir)
            project_dir.mkdir(parents=True, exist_ok=True)

            _save_generated_files(project_dir, files)
            zip_filename = f"{folder_name}.zip"
            zip_path = GENERATED_ROOT / zip_filename
            _zip_project_folder(project_dir, zip_path)

            req.generated_folder = folder_name
            req.zip_filename = zip_filename
            req.status = "Completed"
            db.session.commit()

            logger.info("Project generated for request %s at %s", req.id, zip_path)
            _send_status_email(req, completed=True)
        except Exception as exc:
            req.status = "Pending"
            req.error_message = str(exc)[:1200]
            db.session.commit()
            logger.error("Generation worker failed for request %s: %s", request_id, traceback.format_exc())


def _enqueue_generation(request_id: int) -> None:
    thread = threading.Thread(target=_generation_worker, args=(request_id,), daemon=True)
    thread.start()


def _can_access_request(req: ProjectRequest) -> bool:
    if not current_user.is_authenticated:
        return False
    return current_user.is_admin or req.user_id == current_user.id


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not all([name, email, password, confirm]):
            flash("Please fill all fields.", "error")
        elif len(name) > 120 or len(email) > 120:
            flash("Input is too long.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
        else:
            hashed = generate_password_hash(password)
            base_username = re.sub(r"[^a-zA-Z0-9_]+", "", (name or "").lower())[:24] or "user"
            candidate = base_username
            i = 2
            while User.query.filter_by(username=candidate).first() is not None:
                candidate = f"{base_username}{i}"
                i += 1
            user = User(
                username=candidate[:120],
                name=name[:120],
                email=email[:120],
                password=hashed,
                password_hash=hashed,
                is_verified=True,
                role="user",
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard" if current_user.is_admin else "dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and _verify_user_password(user, password):
            login_user(user)
            return redirect(url_for("admin_dashboard" if user.is_admin else "dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("login.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.is_admin and _verify_user_password(user, password):
            login_user(user)
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    rows = ProjectRequest.query.filter_by(user_id=current_user.id).order_by(ProjectRequest.created_at.desc()).all()
    return render_template("dashboard.html", requests=rows)


@app.route("/studio")
@login_required
def studio():
    _require_admin()
    return redirect(url_for("admin_dashboard"))


@app.route("/order", methods=["GET", "POST"])
@login_required
def order():
    if current_user.is_admin:
        flash("Admin cannot submit MVP order.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        idea = request.form.get("idea", "").strip()
        framework = request.form.get("framework", "").strip()
        database = request.form.get("database", "").strip()
        plan = request.form.get("plan", "").strip()
        extra = request.form.get("extra", "").strip()

        if not all([name, email, idea, framework, database, plan]):
            flash("Please fill all fields.", "error")
            return render_template("order.html")
        if len(name) > 120 or len(email) > 120 or len(phone) > 50 or len(idea) > 8000 or len(extra) > 5000:
            flash("Input is too long.", "error")
            return render_template("order.html")
        if framework not in ALLOWED_FRAMEWORKS or database not in ALLOWED_DATABASES or plan not in ALLOWED_PLANS:
            flash("Invalid form values submitted.", "error")
            return render_template("order.html")

        req = ProjectRequest(
            user_id=current_user.id,
            name=name[:120],
            email=email[:120],
            phone=phone[:50] if phone else None,
            idea=idea,
            framework=framework,
            database=database,
            plan=plan,
            package=plan,
            extra=extra if extra else None,
            status="Pending",
        )
        db.session.add(req)
        db.session.commit()
        logger.info("New project request created: id=%s user=%s", req.id, current_user.email)
        _send_new_order_alert(req)
        _enqueue_generation(req.id)
        flash("Request submitted. AI is building your SaaS MVP...", "success")
        return redirect(url_for("dashboard"))

    return render_template("order.html")


@app.route("/project/<int:req_id>/download")
@login_required
def download_project(req_id: int):
    req = ProjectRequest.query.get_or_404(req_id)
    if not _can_access_request(req):
        abort(403)
    if not req.zip_filename:
        flash("Project ZIP is not ready yet.", "error")
        return redirect(url_for("dashboard" if not current_user.is_admin else "admin_dashboard"))
    zip_path = GENERATED_ROOT / req.zip_filename
    if not zip_path.exists():
        flash("Generated ZIP file missing on server.", "error")
        return redirect(url_for("dashboard" if not current_user.is_admin else "admin_dashboard"))
    return send_file(zip_path, as_attachment=True, download_name=req.zip_filename)


@app.route("/project/<int:req_id>/delete", methods=["POST"])
@login_required
def delete_project(req_id: int):
    req = ProjectRequest.query.get_or_404(req_id)
    if not _can_access_request(req):
        abort(403)
    if req.generated_folder:
        folder = GENERATED_ROOT / req.generated_folder
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)
    if req.zip_filename:
        zip_file = GENERATED_ROOT / req.zip_filename
        if zip_file.exists():
            try:
                zip_file.unlink()
            except Exception:
                pass
    db.session.delete(req)
    db.session.commit()
    flash("Project request deleted.", "success")
    return redirect(url_for("dashboard" if not current_user.is_admin else "admin_dashboard"))


@app.route("/request/<int:req_id>/messages", methods=["GET", "POST"])
@login_required
def request_messages(req_id: int):
    req = ProjectRequest.query.get_or_404(req_id)
    if not _can_access_request(req):
        abort(403)

    if request.method == "POST":
        text_value = request.form.get("message", "").strip()
        if not text_value:
            flash("Message cannot be empty.", "error")
            return redirect(url_for("request_messages", req_id=req.id))
        if len(text_value) > 2000:
            flash("Message is too long.", "error")
            return redirect(url_for("request_messages", req_id=req.id))

        sender_role = "admin" if current_user.is_admin else "customer"
        db.session.add(
            RequestMessage(
                request_id=req.id,
                user_id=current_user.id,
                sender_role=sender_role,
                message=text_value,
            )
        )
        db.session.commit()
        flash("Message sent.", "success")
        return redirect(url_for("request_messages", req_id=req.id))

    messages = RequestMessage.query.filter_by(request_id=req.id).order_by(RequestMessage.created_at.asc()).all()
    return render_template("request_messages.html", req=req, messages=messages)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()
        if not all([name, email, message]):
            flash("Please fill all fields.", "error")
            return render_template("contact.html")
        if len(name) > 120 or len(email) > 120 or len(message) > 5000:
            flash("Input is too long.", "error")
            return render_template("contact.html")
        db.session.add(ContactMessage(name=name[:120], email=email[:120], message=message))
        db.session.commit()
        flash("Message received. We will get back to you.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/blog")
def blog():
    posts = [
        {
            "title": "How to Validate a SaaS Idea in 24-48 Hours",
            "summary": "Use AI-assisted scoping, fast wireframes, and rapid backend scaffolding.",
        },
        {
            "title": "Flask vs FastAPI vs Django for MVPs",
            "summary": "Choose based on speed, ecosystem, and expected complexity.",
        },
        {
            "title": "What Makes an MVP Deploy-Ready",
            "summary": "Authentication, database setup, env configs, and CI/deploy basics.",
        },
    ]
    return render_template("blog.html", posts=posts)


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/refund")
def refund():
    return render_template("refund.html")


@app.route("/admin")
@login_required
def admin_root():
    _require_admin()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    _require_admin()
    rows = ProjectRequest.query.order_by(ProjectRequest.created_at.desc()).all()
    return render_template("admin_dashboard.html", requests=rows)


@app.route("/admin/request/<int:req_id>/status", methods=["POST"])
@login_required
def update_request_status(req_id: int):
    _require_admin()
    req = ProjectRequest.query.get_or_404(req_id)
    next_status = request.form.get("status", "").strip()
    if next_status not in ALLOWED_STATUSES:
        flash("Invalid status.", "error")
        return redirect(url_for("admin_dashboard"))

    req.status = next_status
    db.session.commit()
    _send_status_email(req, completed=next_status in {"Completed", "Delivered"})
    flash("Status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/request/<int:req_id>/generate", methods=["POST"])
@login_required
def admin_generate_project(req_id: int):
    _require_admin()
    req = ProjectRequest.query.get_or_404(req_id)
    if req.status == "Generating":
        flash("Project is already generating.", "error")
        return redirect(url_for("admin_dashboard"))
    req.status = "Pending"
    req.error_message = None
    db.session.commit()
    _enqueue_generation(req.id)
    flash("Generation started.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/download-all")
@login_required
def admin_download_all_projects():
    _require_admin()
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for req in ProjectRequest.query.filter(ProjectRequest.zip_filename.isnot(None)).all():
            zip_path = GENERATED_ROOT / str(req.zip_filename)
            if zip_path.exists():
                zf.write(zip_path, arcname=zip_path.name)
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="all-generated-projects.zip", mimetype="application/zip")


@app.route("/admin/export.csv")
@login_required
def export_requests_csv():
    _require_admin()
    rows = ProjectRequest.query.order_by(ProjectRequest.created_at.desc()).all()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "ID",
            "User",
            "Name",
            "Email",
            "Phone",
            "Idea",
            "Framework",
            "Database",
            "Plan",
            "Package",
            "Extra",
            "Status",
            "Zip",
            "Created At",
            "Updated At",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.owner.email if r.owner else "",
                r.name,
                r.email,
                r.phone or "",
                r.idea,
                r.framework,
                r.database,
                r.plan,
                r.package or "",
                r.extra or "",
                r.status,
                r.zip_filename or "",
                r.created_at.isoformat(),
                r.updated_at.isoformat(),
            ]
        )
    response = make_response(stream.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=fuzail-labs-requests.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@app.errorhandler(403)
def forbidden(_e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        _run_startup_migrations()
        _ensure_admin()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
