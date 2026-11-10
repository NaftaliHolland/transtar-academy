from django.core.paginator import Paginator
from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from core.blocks import ARTICLE_BLOCKS
from core.models import BasePage


class EventPage(BasePage):
    seo_description_field = "summary"

    start_datetime = models.DateTimeField("starts")
    end_datetime = models.DateTimeField("ends", null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    summary = models.TextField(max_length=400, help_text="Short description shown in listings.")
    image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    body = StreamField(ARTICLE_BLOCKS, blank=True)
    registration_url = models.URLField(blank=True, help_text="Optional external registration or information link.")
    registration_label = models.CharField(max_length=60, blank=True, default="Register")
    featured = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("start_datetime"), FieldPanel("end_datetime")]),
                FieldPanel("location"),
                FieldPanel("featured"),
            ],
            heading="When and where",
        ),
        FieldPanel("summary"),
        FieldPanel("image"),
        FieldPanel("body"),
        MultiFieldPanel([FieldPanel("registration_url"), FieldPanel("registration_label")], heading="Registration"),
    ]
    search_fields = Page.search_fields + [index.SearchField("summary"), index.SearchField("location"), index.SearchField("body")]

    parent_page_types = ["events.EventsIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "event"

    def clean(self):
        super().clean()
        if self.end_datetime and self.start_datetime and self.end_datetime < self.start_datetime:
            from django.core.exceptions import ValidationError

            raise ValidationError({"end_datetime": "The end must be after the start."})

    @property
    def ends_at(self):
        return self.end_datetime or self.start_datetime

    @property
    def is_upcoming(self):
        return self.ends_at >= timezone.now()

    @property
    def spans_days(self):
        if not self.end_datetime:
            return False
        return timezone.localtime(self.end_datetime).date() != timezone.localtime(self.start_datetime).date()

    def get_meta_image(self):
        return self.social_image or self.image


def _events():
    return (
        EventPage.objects.live().public()
        .select_related("image")
        .annotate(ends_at_db=Coalesce("end_datetime", "start_datetime"))
    )


def upcoming_events():
    """Events that have not finished yet, soonest first."""
    return _events().filter(ends_at_db__gte=timezone.now()).order_by("start_datetime")


def past_events():
    """Events that have finished, most recent first."""
    return _events().filter(ends_at_db__lt=timezone.now()).order_by("-start_datetime")


class EventsIndexPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = ["events.EventPage"]
    paginate_by = 9

    class Meta:
        verbose_name = "events listing page"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        showing_past = request.GET.get("when") == "past"
        events = (past_events() if showing_past else upcoming_events()).child_of(self)
        context.update(
            showing_past=showing_past,
            page_obj=Paginator(events, self.paginate_by).get_page(request.GET.get("page")),
        )
        return context
