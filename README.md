# Glory High School website

Django 5.2 + Wagtail 7.0 (LTS) + Tailwind CSS 4. The visual design comes from `docs/reference/index.html`.

## Local setup
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
(cd theme && npm install && npm run build)      # compiles Tailwind to theme/static/theme/css/site.css
python manage.py migrate
python manage.py seed_demo                      # placeholder pages, menus and images (use --reset to rebuild)
python manage.py createsuperuser
python manage.py runserver                      # site on :8000, admin on /admin/
```
Run `npm run dev` in `theme/` while editing templates. Run tests with `python manage.py test`.

## Editing the site (Wagtail admin)
- **Settings > Site settings**: name, logo, favicon, contact details, social links, alert bar, footer, default SEO.
- **Settings > Navigation**: header menu (with dropdowns), top-bar links, footer columns.
- **Pages**: Home (hero + reorderable sections), content pages (About, Academics, Admissions, Facilities, Student life, Policies), FAQ, News, Events, Gallery, Contact.
- **Enquiries** (side menu): contact form submissions, exportable, with a "handled" flag.
- Replace the generated placeholder images and all text marked "Demonstration content".

## Apps
`core` (settings, navigation, blocks, content/FAQ pages), `home`, `news`, `events`, `gallery`, `contact`, `search`; `theme` holds Tailwind, fonts and JS.

## Tailwind
Tailwind v4 via `@tailwindcss/cli`. `theme/src/input.css` scans only project folders. Editor-selected classes are full strings in `core/blocks.py` or templates, never built by concatenation. Fonts are self-hosted (Barlow Condensed, Inter, Mrs Saint Delafield).
Deliberate change: small white text on the original `#5b7bce` failed 4.5:1 contrast, so tiles and staff cards use `#4a67b8` (`periwinkle-deep`).

## Production
Set environment variables: `DJANGO_SETTINGS_MODULE=glorysite.settings.production`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` (e.g. `postgres://user:pass@host/db`), `WAGTAILADMIN_BASE_URL`, `MEDIA_ROOT`, `TIME_ZONE`, `CONTACT_RECIPIENT_EMAIL`, and SMTP: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`.
```bash
(cd theme && npm ci && npm run build)
python manage.py migrate && python manage.py collectstatic --noinput
gunicorn glorysite.wsgi
```
- Static files are served by WhiteNoise; serve `MEDIA_ROOT` from your web server or object storage.
- Set `REDIS_URL` (and `pip install redis`) so contact-form rate limits are shared across workers. Set `TRUSTED_PROXY_COUNT` when behind proxies so the real client IP is used.
- `X_FRAME_OPTIONS` stays `SAMEORIGIN` because Wagtail's preview panel needs it.
- Contact form protection: CSRF, hidden honeypot, signed time-to-fill token, per-IP rate limit (`CONTACT_RATE_LIMIT`, `CONTACT_RATE_WINDOW`). Enquiries are stored even if email fails.
