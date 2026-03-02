# Security Stage 2: AuthZ/AuthN Plan

## Implemented in code
- Mutating endpoints converted to `POST` + CSRF protection:
  - `upgrade`
  - `subscribe_category` / `unsubscribe_category`
  - `subscribe_author` / `unsubscribe_author`
- `like_post` now requires authenticated user.
- `test-email` endpoint restricted to staff users and `POST` only.
- `allauth` rate limits tightened in `news/settings.py`.

## Access-control audit (current status)
- `NewsCreateView` / `ArticleCreateView`: `LoginRequiredMixin` + `UserPassesTestMixin` (authors group only) -> OK
- `PostUpdateView`: queryset restricted to `author__user=request.user` -> OK
- `profile` / email/password security pages: login required -> OK
- subscription/reaction endpoints: now login + POST only -> OK

## 2FA and CAPTCHA roadmap
1. Add 2FA via `django-allauth` MFA flow (recommended) or `django-otp`.
2. Require 2FA for staff/admin accounts first.
3. Add CAPTCHA on repeated failed login attempts:
   - Option A: `django-simple-captcha` on login form after N failures.
   - Option B: reCAPTCHA/hCaptcha for public auth endpoints.
4. Add alerting/logging for suspicious auth activity:
   - repeated failures
   - unusual IP bursts
   - password reset abuse

## Deployment checklist
- Set production env from `.env.production.example`.
- Run:
  - `python manage.py check --deploy`
- Validate HTTPS redirect and HSTS on real domain behind Nginx.
