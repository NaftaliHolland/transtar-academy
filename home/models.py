from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.models import Page
from wagtail.search import index

from core.blocks import SECTION_BLOCKS, LinkBlock
from core.models import BasePage


class HeroTileBlock(blocks.StructBlock):
    image = ImageBlock()
    title = blocks.CharBlock(max_length=60)
    link = LinkBlock(required=False)

    class Meta:
        label_format = "{title}"


class HomePage(BasePage):
    seo_description_field = "hero_tagline"

    hero_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Large campus photo behind the header. At least 1920 pixels wide.",
    )
    hero_heading = models.TextField(
        default="Unlock Your\nFuture Success", max_length=120,
        help_text="Press Enter to start a new line.",
    )
    hero_tagline = models.CharField(max_length=120, blank=True, default="High School Redefined for Success")
    hero_tiles = StreamField([("tile", HeroTileBlock())], blank=True, max_num=3)
    body = StreamField(SECTION_BLOCKS, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [FieldPanel("hero_image"), FieldPanel("hero_heading"), FieldPanel("hero_tagline"), FieldPanel("hero_tiles")],
            heading="Hero",
        ),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [index.SearchField("hero_tagline"), index.SearchField("body")]

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "core.StandardPage", "core.FAQPage", "news.NewsIndexPage", "events.EventsIndexPage",
        "gallery.GalleryIndexPage", "contact.ContactPage",
    ]

    class Meta:
        verbose_name = "home page"

    def get_meta_title(self):
        return self.seo_title  # the school name is used when empty

    @property
    def hero_heading_lines(self):
        return [line.strip() for line in self.hero_heading.splitlines() if line.strip()]
