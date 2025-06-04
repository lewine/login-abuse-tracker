# ────────────────────────────────────────────────────────────────────────────
# Stage 1: Build the React front end
# ────────────────────────────────────────────────────────────────────────────
FROM node:18-alpine AS frontend-build

WORKDIR /usr/src/app

# 1) Copy front-end package files, install deps
COPY login-abuse-ui/package.json login-abuse-ui/package-lock.json ./login-abuse-ui/
WORKDIR /usr/src/app/login-abuse-ui
RUN npm ci

# 2) Copy full React source and build into /usr/src/app/login-abuse-ui/dist
COPY login-abuse-ui/. ./
RUN npm run build


# ────────────────────────────────────────────────────────────────────────────
# Stage 2: Build the Python/Flask back end (and include React build)
# ────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# 1) Install any OS‐level dependencies (e.g. build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2) Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/appuser

# 3) Create a non-root user and switch to its home directory
RUN useradd --create-home appuser
WORKDIR /home/appuser

# 4) Copy requirements.txt and install Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy entire repository (Flask code, tracker, simulate_api, tests, etc.)
COPY . ./

# 6) Copy React’s production build from Stage 1 into ./frontend-dist
COPY --from=frontend-build /usr/src/app/login-abuse-ui/dist ./frontend-dist

# 7) Expose Flask’s port
EXPOSE 5000

# 8) Tell Flask how to run
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

CMD ["flask", "run"]
