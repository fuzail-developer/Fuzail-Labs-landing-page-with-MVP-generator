# Deploy Helper

## One-Click Links

- Render: https://render.com/deploy?repo=<YOUR_GITHUB_REPO_URL>
- Railway: https://railway.app/new?referralCode=<YOUR_CODE>

## Quick Commands

```bash
# 1) Push project to GitHub first
git init
git add .
git commit -m "deploy prep"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

```bash
# 2) Required env vars in hosting dashboard
SECRET_KEY=<generate-random-secret>
DATABASE_URL=sqlite:///app.db
OPENAI_API_KEY=<optional>
```

## Procfile

This project already includes:

```text
web: gunicorn app:app
```

## Automation Files

- Dockerfile
- docker-compose.yml
- railway.json
- vercel.json

## App Name

`build-a-modern-saas-landing-page-website-for-a-service-called-fu`
