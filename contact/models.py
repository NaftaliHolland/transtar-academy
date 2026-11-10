from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from core.blocks import RichTextSectionBlock, InfoCardsBlock
from core.models import BasePage

from django.conf import settings
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from core.ratelimit import client_ip, hit

from .forms import CATEGORY_CHOICES, ContactForm, make_token


class ContactSubmission(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False, editable=False)
    handled = models.BooleanField(default=False, help_text="Tick once someone has replied.")

    panels = [
        FieldPanel("name"),
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("category"),
        FieldPanel("message"),
        FieldPanel("handled"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "enquiry"

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ContactPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)
    body = StreamField(
        [("text", RichTextSectionBlock()), ("info_cards", InfoCardsBlock())],
        blank=True,
        help_text="Optional extra content shown beside the form. Phone, email and addresses come from Site settings.",
    )
    recipient_email = models.EmailField(
        blank=True, help_text="Where enquiries are emailed. Falls back to the server setting, then the school email."
    )
    success_message = models.CharField(
        max_length=240, default="Thank you. We have received your message and will reply soon."
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("recipient_email"),
        FieldPanel("success_message"),
    ]

    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = []
    max_count = 1

    class Meta:
        verbose_name = "contact page"

    def serve(self, request, *args, **kwargs):
        from .services import save_and_notify

        if request.method == "POST":
            form = ContactForm(request.POST)
            status = 200
            if form.is_valid():
                if hit("contact", client_ip(request), settings.CONTACT_RATE_LIMIT, settings.CONTACT_RATE_WINDOW):
                    form.add_error(None, "You have sent several messages recently. Please try again later or call the school.")
                    status = 429
                else:
                    # Bots get the same confirmation but nothing is stored or sent.
                    if not form.is_spam:
                        save_and_notify(self, request, form.cleaned_data)
                    return HttpResponseRedirect(self.url + "?sent=1")
            elif form.token_expired:
                data = request.POST.copy()
                data["started"] = make_token()
                form = ContactForm(data)
                form.is_valid()
                status = 400
            else:
                status = 400
            return self.render_form(request, form, status)

        initial = {}
        wanted = request.GET.get("category")
        if wanted in dict(CATEGORY_CHOICES):
            initial["category"] = wanted
        return self.render_form(request, ContactForm(initial=initial), 200)

    def render_form(self, request, form, status):
        context = self.get_context(request)
        context.update(form=form, sent=request.GET.get("sent") == "1" and request.method == "GET")
        response = TemplateResponse(request, self.get_template(request), context)
        response.status_code = status
        return response
