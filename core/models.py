from django.db import models
from django.utils.html import strip_tags
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from .blocks import (
    FAQCategoryBlock,
    FooterColumnBlock,
    LinkBlock,
    MenuItemBlock,
    SECTION_BLOCKS,
    SocialLinkBlock,
)


class BasePage(Page):
    """Abstract base for every page type: adds a social sharing image and SEO helpers."""

    social_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Shown when the page is shared. Falls back to the default in Site settings.",
    )

    promote_panels = Page.promote_panels + [FieldPanel("social_image")]

    class Meta:
        abstract = True

    # Overridden by page types with an intro/summary field.
    seo_description_field = "intro"

    def get_meta_description(self):
        if self.search_description:
            return self.search_description
        text = strip_tags(str(getattr(self, self.seo_description_field, "") or "")).strip()
        return text[:160]

    def get_meta_title(self):
        return self.seo_title or self.title

    def get_meta_image(self):
        return self.social_image


@register_setting(icon="cog")
class SiteSettings(BaseSiteSetting):
    school_name = models.CharField(max_length=120, default="Glory High School")
    tagline = models.CharField(max_length=160, blank=True, default="High school redefined for success")
    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="School emblem shown in the header and footer.",
    )
    logo_wordmark = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Optional wordmark image shown beside the emblem. When empty, the school name is shown as text.",
    )
    favicon = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Square image, at least 192 by 192 pixels.",
    )

    phone = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    admissions_email = models.EmailField(blank=True)
    physical_address = models.TextField(blank=True)
    postal_address = models.TextField(blank=True)
    office_hours = models.TextField(blank=True, help_text="One line per entry, for example 'Mon to Fri: 8:00 to 16:30'.")
    map_url = models.URLField(blank=True, help_text="Link to the school's location on a map service.")

    social_links = StreamField([("link", SocialLinkBlock())], blank=True, max_num=8)

    alert_message = models.CharField(max_length=240, blank=True, help_text="Leave empty to hide the alert bar.")
    alert_link_page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    alert_link_text = models.CharField(max_length=60, blank=True)

    cta_text = models.CharField(max_length=60, blank=True, default="Apply now")
    cta_page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Admissions call to action shown in the footer.",
    )

    footer_text = models.TextField(blank=True, help_text="Short description shown in the footer.")
    copyright_text = models.CharField(
        max_length=160, blank=True, help_text="Shown after the year and school name, for example 'All rights reserved.'"
    )

    default_meta_description = models.CharField(max_length=160, blank=True)
    default_social_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    edit_handler = TabbedInterface(
        [
            ObjectList(
                [
                    FieldPanel("school_name"),
                    FieldPanel("tagline"),
                    FieldPanel("logo"),
                    FieldPanel("logo_wordmark"),
                    FieldPanel("favicon"),
                ],
                heading="Branding",
            ),
            ObjectList(
                [
                    FieldPanel("phone"),
                    FieldPanel("email"),
                    FieldPanel("admissions_email"),
                    FieldPanel("physical_address"),
                    FieldPanel("postal_address"),
                    FieldPanel("office_hours"),
                    FieldPanel("map_url"),
                    FieldPanel("social_links"),
                ],
                heading="Contact and social",
            ),
            ObjectList(
                [
                    MultiFieldPanel(
                        [FieldPanel("alert_message"), FieldPanel("alert_link_page"), FieldPanel("alert_link_text")],
                        heading="Alert bar",
                    ),
                    MultiFieldPanel([FieldPanel("cta_text"), FieldPanel("cta_page")], heading="Admissions call to action"),
                    FieldPanel("footer_text"),
                    FieldPanel("copyright_text"),
                ],
                heading="Banner and footer",
            ),
            ObjectList(
                [FieldPanel("default_meta_description"), FieldPanel("default_social_image")],
                heading="Default SEO",
            ),
        ]
    )

    class Meta:
        verbose_name = "Site settings"

    @property
    def office_hours_lines(self):
        return [line.strip() for line in self.office_hours.splitlines() if line.strip()]


@register_setting(icon="list-ul")
class NavigationSettings(BaseSiteSetting):
    header_menu = StreamField([("item", MenuItemBlock())], blank=True, help_text="Main navigation. Add dropdown links under an item to create a submenu.")
    utility_menu = StreamField([("link", LinkBlock())], blank=True, max_num=4, help_text="Small links in the top bar.")
    footer_columns = StreamField([("column", FooterColumnBlock())], blank=True, max_num=4)

    panels = [FieldPanel("header_menu"), FieldPanel("utility_menu"), FieldPanel("footer_columns")]

    class Meta:
        verbose_name = "Navigation"


class StandardPage(BasePage):
    """General content page used for About, Academics, Admissions, Facilities, Student Life and Policies."""

    intro = models.TextField(blank=True, max_length=400, help_text="Short summary shown in the page header.")
    header_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Optional photo behind the page header.",
    )
    body = StreamField(SECTION_BLOCKS, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("header_image"),
        FieldPanel("body"),
    ]
    search_fields = Page.search_fields + [index.SearchField("intro"), index.SearchField("body")]

    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = ["core.StandardPage", "core.FAQPage", "news.NewsIndexPage", "events.EventsIndexPage",
                     "gallery.GalleryIndexPage", "contact.ContactPage"]

    class Meta:
        verbose_name = "content page"


class FAQPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)
    categories = StreamField([("category", FAQCategoryBlock())], blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("categories")]
    search_fields = Page.search_fields + [index.SearchField("intro"), index.SearchField("categories")]

    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = []

    class Meta:
        verbose_name = "FAQ page"
