import re
import time

from django import forms
from django.conf import settings
from django.core import signing

SALT = "contact-form"
MAX_AGE = 60 * 60 * 2

CATEGORY_CHOICES = [
    ("general", "General enquiry"),
    ("admissions", "Admissions"),
    ("academics", "Academics"),
    ("fees", "Fees and payments"),
    ("other", "Something else"),
]

PHONE_RE = re.compile(r"^[0-9+()\-\s.]{6,30}$")


def make_token():
    return signing.dumps(time.time(), salt=SALT)


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Your name")
    email = forms.EmailField(label="Email address")
    phone = forms.CharField(max_length=30, required=False, label="Phone number (optional)")
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label="What is your enquiry about?")
    message = forms.CharField(
        min_length=10,
        max_length=3000,
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Message",
    )
    # Spam traps. `website` is hidden from people with CSS; bots tend to fill it in.
    website = forms.CharField(required=False, label="Leave this field empty")
    started = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["website"].widget.attrs.update({"tabindex": "-1", "autocomplete": "off"})
        self.fields["name"].widget.attrs["autocomplete"] = "name"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["phone"].widget.attrs["autocomplete"] = "tel"
        if not self.is_bound:
            self.initial["started"] = make_token()
        self.is_spam = False
        self.token_expired = False

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not PHONE_RE.match(phone):
            raise forms.ValidationError("Enter a phone number using digits, spaces, + or -.")
        return phone

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            self.is_spam = True
            return cleaned
        token = cleaned.get("started", "")
        try:
            started_at = signing.loads(token, salt=SALT, max_age=MAX_AGE)
        except signing.SignatureExpired:
            self.token_expired = True
            raise forms.ValidationError("This form timed out. Check your message and send it again.")
        except signing.BadSignature:
            self.is_spam = True
            return cleaned
        if time.time() - float(started_at) < getattr(settings, "CONTACT_MIN_FILL_SECONDS", 3):
            self.is_spam = True
        return cleaned
