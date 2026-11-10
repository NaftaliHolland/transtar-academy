import logging

from django.conf import settings
from django.core.mail import EmailMessage

from core.models import SiteSettings

from .models import ContactSubmission

logger = logging.getLogger(__name__)


def recipient_for(page, request):
    return (
        page.recipient_email
        or settings.CONTACT_RECIPIENT_EMAIL
        or SiteSettings.for_request(request).email
    )


def save_and_notify(page, request, data):
    """Store an enquiry and email it to the school. A mail failure never loses the enquiry."""
    submission = ContactSubmission.objects.create(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        category=data["category"],
        message=data["message"],
    )
    to = recipient_for(page, request)
    if not to:
        return submission
    school = SiteSettings.for_request(request).school_name
    subject = " ".join(f"[{school}] {submission.get_category_display()}: {submission.name}".split())[:200]
    body = (
        f"Name: {submission.name}\nEmail: {submission.email}\nPhone: {submission.phone or '-'}\n"
        f"Topic: {submission.get_category_display()}\n\n{submission.message}\n"
    )
    try:
        EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [to], reply_to=[submission.email]).send()
        submission.email_sent = True
        submission.save(update_fields=["email_sent"])
    except Exception:  # noqa: BLE001 - SMTP errors vary; the enquiry is already stored
        logger.exception("Could not send enquiry email for submission %s", submission.pk)
    return submission
