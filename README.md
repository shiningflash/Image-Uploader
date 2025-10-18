# Django Image Upload Service

This project is a simple Django application that allows users to upload an image anonymously, view it via a unique shareable URL, and delete it if they are the original uploader. Each IP address is limited to 10 uploads per day. The application is fully containerized with Docker.

---

## Requirements

* Python 3.8+
* Docker and Docker Compose (for containerized setup)

---

## Project Setup

### 1. Run with Docker (recommended)

Build the image and run the container:

```bash
unzip django_exercise.zip
cd django_exercise
docker build -t exercise .
docker run --rm -p 8000:8000 -v $(pwd):/app exercise
```

The application will be available at:
[http://localhost:8000](http://localhost:8000)

---

### 2. Run Locally (without Docker)

If you prefer to run it locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open the application at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Create Superuser (for Django Admin)

To access the Django admin panel, you need a superuser account.
Create one by running:

**Using Docker Compose:**

```bash
docker-compose run --rm web python manage.py createsuperuser
```

**Or locally:**

```bash
python manage.py createsuperuser
```

Then log in to the admin panel at:
[http://localhost:8000/admin](http://localhost:8000/admin)

## Run tests

```bash
python manage.py test images -v 2  # locally 
docker-compose run --rm web python manage.py test images -v 2  # using docker compose
```

---

## Endpoints

| Endpoint                     | Method    | Description                                          |
| ---------------------------- | --------- | ---------------------------------------------------- |
| `/`                          | GET, POST | Upload an image (max 10 uploads per day per IP)      |
| `/image/<public_id>/`        | GET       | View the uploaded image and upload date              |
| `/image/<public_id>/delete/` | POST      | Delete the image (only by original uploader session) |

---

## Example Usage

1. Visit `/` to access the image upload form.
2. Upload an image (no authentication required).
3. After a successful upload, you are redirected to `/image/<public_id>/`, where:

   * The uploaded image and upload date are shown.
   * A delete button appears if your session owns the image.
4. Share `/image/<public_id>/` with anyone — it’s publicly accessible.
5. Only the original uploader session can delete the image.

---

## Next Plan

This project is currently an MVP focused on correctness and clarity.

### Implemented

* ✔️ Add unit tests for core functionalities
* ✔️ `is_daily_quota_exceeded()` (simple per-day quota check based on date)
* ✔️ `is_24h_quota_exceeded()` (rolling 24 hours window based quota check)
* ✔️ Image size validation Middleware (max 5 MB)
* ✔️ Quota Check Middleware
* ✔️ Request Logging Middleware
* ✔️ File Size Limit Middleware (upto 5 MB)
* ✔️ Log file generation (automatic, log every request) - check `logs/app.log`
* ✔️ Pagination or listing API: Add an endpoint to list a user’s uploaded images with pagination, making it useful beyond single-file cases

### Planned Improvements

* [ ] Use user authentication + ownership field to ensure that only the original uploader can delete the image
* [ ] CI/CD setup: GitHub Actions or GitLab CI pipeline for linting, tests, and Docker build
* [ ] Storage: Move image files to S3 (or any S3-compatible storage like MinIO, DigitalOcean Spaces) using **django-storages** + **boto3**
* [ ] IP quota tracking: Replace DB queries with Redis and 24h key expiration
* [ ] Database: Switch to PostgreSQL with better indexing
* [ ] For large datasets, consider partitioning by month or day
* [ ] Async uploads: Offload uploads to background workers (Celery + S3 signed URLs)
* [ ] CDN caching: Serve images via CloudFront or Cloudflare
* [ ] Content-Type validation: Ensure uploaded files are real images (e.g., check MIME type + Pillow verification) to prevent malicious file uploads
* [ ] Rate limiting / throttling: Beyond the 10-per-IP rule, add Django middleware or a proxy-level rate limiter (e.g., NGINX or Cloudflare) to prevent abuse
* [ ] HTTPS & secure headers: Enforce HTTPS and add headers like Content-Security-Policy and X-Content-Type-Options
* [ ] Multiple file upload: Extend the form to support multiple images at once
* [ ] Thumbnail preview: Generate a thumbnail for faster display
* [ ] Monitoring: Use Prometheus + Grafana to track upload counts and quota rejections

---
