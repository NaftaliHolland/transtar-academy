import time

from django.core import mail, signing
from django.core.cache import cache
from django.test import override_settings

from contact.forms import SALT
from contact.models import ContactPage, ContactSubmission
from core.tests.test_site import SeededSiteTestCase


def token(age=10):
    return signing.dumps(time.time() - age, salt=SALT)


@override_settings(CONTACT_RECIPIENT_EMAIL="office@example.org")
class ContactFormTests(SeededSiteTestCase):
    def setUp(self):
        cache.clear()
        self.url = ContactPage.objects.get().url

    def data(self, **overrides):
        data = {"name": "Parent Example", "email": "parent@example.com", "phone": "+254 700 000000",
                "category": "admissions", "message": "I would like to visit the school.", "website": "", "started": token()}
        data.update(overrides)
        return data

    def test_get_shows_form_with_csrf_and_honeypot(self):
        response = self.client.get(self.url, {"category": "fees"})
        self.assertContains(response, 'name="message"')
        self.assertContains(response, 'name="website"')
        self.assertEqual(response.context["form"].initial["category"], "fees")

    def test_valid_submission_is_stored_and_emailed(self):
        response = self.client.post(self.url, self.data())
        self.assertRedirects(response, self.url + "?sent=1", fetch_redirect_response=False)
        self.assertEqual(ContactSubmission.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["office@example.org"])
        self.assertEqual(mail.outbox[0].reply_to, ["parent@example.com"])
        self.assertContains(self.client.get(self.url + "?sent=1"), "Message sent")

    def test_invalid_submission_shows_accessible_errors(self):
        response = self.client.post(self.url, self.data(email="nope", message="short"))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'role="alert"', status_code=400)
        self.assertContains(response, 'aria-invalid="true"', status_code=400)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_bad_phone_rejected(self):
        response = self.client.post(self.url, self.data(phone="call me maybe"))
        self.assertEqual(response.status_code, 400)

    def test_honeypot_discards_silently(self):
        response = self.client.post(self.url, self.data(website="http://spam.example"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactSubmission.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_instant_submission_discarded(self):
        response = self.client.post(self.url, self.data(started=token(age=0)))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_tampered_token_discarded(self):
        response = self.client.post(self.url, self.data(started="garbage"))
        self.assertEqual(ContactSubmission.objects.count(), 0)
        self.assertEqual(response.status_code, 302)

    def test_expired_token_asks_to_resend_with_fresh_token(self):
        old = signing.dumps(time.time() - 10, salt=SALT)
        with override_settings():
            from contact import forms

            original = forms.MAX_AGE
            forms.MAX_AGE = -1
            try:
                response = self.client.post(self.url, self.data(started=old))
            finally:
                forms.MAX_AGE = original
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "timed out", status_code=400)

    @override_settings(CONTACT_RATE_LIMIT=2)
    def test_rate_limit(self):
        for _ in range(2):
            self.assertEqual(self.client.post(self.url, self.data()).status_code, 302)
        blocked = self.client.post(self.url, self.data())
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(ContactSubmission.objects.count(), 2)

    def test_mail_failure_keeps_enquiry(self):
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="127.0.0.1", EMAIL_PORT=1):
            response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 302)
        submission = ContactSubmission.objects.get()
        self.assertFalse(submission.email_sent)

    def test_newline_in_name_cannot_inject_headers(self):
        self.client.post(self.url, self.data(name="Eve\nBcc: victim@example.com"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("\n", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].bcc, [])
