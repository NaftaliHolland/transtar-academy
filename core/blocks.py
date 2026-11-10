"""Reusable StreamField blocks.

Every block renders through a template in ``core/templates/core/blocks``. Editors only get choices that
cannot break the design (tone, image position, alignment); the full class names live in the Python
constants below so Tailwind's source scan always sees them.
"""
from django.forms.utils import ErrorList
from wagtail import blocks
from wagtail.blocks import StructBlockValidationError
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageBlock

INLINE_FEATURES = ["bold", "italic", "link"]
RICH_FEATURES = ["bold", "italic", "h3", "h4", "ol", "ul", "link", "document-link", "hr"]

TONE_CHOICES = [("white", "White"), ("mist", "Light blue"), ("navy", "Navy")]
TONE_SURFACE = {
    "white": "bg-white text-ink",
    "mist": "bg-mist text-ink",
    "navy": "bg-navy text-white",
}
TONE_BUTTON = {
    "white": "bg-navy text-white hover:bg-steel",
    "mist": "bg-navy text-white hover:bg-steel",
    "navy": "bg-gold text-ink hover:bg-white",
}


# --------------------------------------------------------------------------- links


class LinkStructValue(blocks.StructValue):
    """Value for a link to either a page or an external URL."""

    @property
    def href(self):
        page = self.get("page")
        if page:
            return page.url if page.live else ""
        return self.get("url") or ""

    @property
    def text(self):
        if self.get("label"):
            return self["label"]
        page = self.get("page")
        return page.title if page else ""

    @property
    def is_external(self):
        return not self.get("page") and bool(self.get("url"))

    @property
    def has_link(self):
        return bool(self.href)


class LinkBlock(blocks.StructBlock):
    label = blocks.CharBlock(required=False, max_length=60, help_text="Defaults to the page title.")
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False, help_text="External address. Ignored when a page is chosen.")

    class Meta:
        icon = "link"
        value_class = LinkStructValue

    def clean(self, value):
        result = super().clean(value)
        if result.get("label") and not (result.get("page") or result.get("url")):
            raise StructBlockValidationError(
                block_errors={"page": ErrorList(["Choose a page or enter a URL."])}
            )
        return result


class MenuItemBlock(LinkBlock):
    children = blocks.ListBlock(LinkBlock(), required=False, label="Dropdown links")

    class Meta:
        icon = "list-ul"

    def clean(self, value):
        # A top-level item may be a label that only opens a dropdown.
        result = blocks.StructBlock.clean(self, value)
        has_link = result.get("page") or result.get("url")
        if not has_link and not (result.get("label") and result.get("children")):
            raise StructBlockValidationError(
                block_errors={"page": ErrorList(["Choose a page or URL, or add a label with dropdown links."])}
            )
        return result


class SocialLinkBlock(blocks.StructBlock):
    platform = blocks.ChoiceBlock(
        choices=[
            ("facebook", "Facebook"),
            ("twitter", "X / Twitter"),
            ("instagram", "Instagram"),
            ("linkedin", "LinkedIn"),
            ("youtube", "YouTube"),
        ]
    )
    url = blocks.URLBlock()

    class Meta:
        icon = "link-external"
        label_format = "{platform}"


class FooterColumnBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=60)
    links = blocks.ListBlock(LinkBlock())

    class Meta:
        icon = "list-ul"
        label_format = "{title}"


# --------------------------------------------------------------------------- tone helper


class ToneStructValue(blocks.StructValue):
    @property
    def surface(self):
        return TONE_SURFACE.get(self.get("tone"), TONE_SURFACE["white"])

    @property
    def button_classes(self):
        return TONE_BUTTON.get(self.get("tone"), TONE_BUTTON["white"])


# --------------------------------------------------------------------------- content blocks


class SectionIntroBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120)
    text = blocks.RichTextBlock(features=INLINE_FEATURES, required=False)
    align = blocks.ChoiceBlock(choices=[("center", "Centred"), ("left", "Left")], default="center")

    class Meta:
        template = "core/blocks/section_intro.html"
        icon = "title"
        label = "Section heading"


class RichTextSectionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    body = blocks.RichTextBlock(features=RICH_FEATURES)
    tone = blocks.ChoiceBlock(choices=TONE_CHOICES, default="white")

    class Meta:
        template = "core/blocks/rich_text_section.html"
        icon = "doc-full"
        label = "Text section"
        value_class = ToneStructValue


class ImageTextBlock(blocks.StructBlock):
    image = ImageBlock()
    heading = blocks.CharBlock(max_length=120)
    text = blocks.RichTextBlock(features=RICH_FEATURES)
    button = LinkBlock(required=False)
    image_position = blocks.ChoiceBlock(choices=[("left", "Left"), ("right", "Right")], default="left")
    tone = blocks.ChoiceBlock(choices=TONE_CHOICES, default="white")

    class Meta:
        template = "core/blocks/image_text.html"
        icon = "image"
        label = "Image and text"
        value_class = ToneStructValue


class TileBlock(blocks.StructBlock):
    image = ImageBlock()
    title = blocks.CharBlock(max_length=80)
    description = blocks.TextBlock(
        required=False,
        max_length=400,
        help_text="When set, the tile opens a dialog showing this text.",
    )
    link = LinkBlock(required=False)

    class Meta:
        label_format = "{title}"


class FeatureTilesBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    tiles = blocks.ListBlock(TileBlock(), min_num=1, max_num=9)

    class Meta:
        template = "core/blocks/feature_tiles.html"
        icon = "grip"
        label = "Image tiles (programs, courses)"


class SplitItemBlock(blocks.StructBlock):
    icon = ImageBlock(required=False, help_text="Optional small illustration or icon.")
    heading = blocks.CharBlock(max_length=80)
    text = blocks.TextBlock(max_length=400)

    class Meta:
        label_format = "{heading}"


class SplitIntroBlock(blocks.StructBlock):
    items = blocks.ListBlock(SplitItemBlock(), min_num=1, max_num=4)
    panel_heading = blocks.CharBlock(max_length=60)
    panel_text = blocks.TextBlock(max_length=600)
    panel_link = LinkBlock(required=False)

    class Meta:
        template = "core/blocks/split_intro.html"
        icon = "form"
        label = "Highlights with welcome panel"


class FacilityMosaicBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80)
    text = blocks.TextBlock(max_length=600)
    images = blocks.ListBlock(ImageBlock(), min_num=2, max_num=6)

    class Meta:
        template = "core/blocks/facility_mosaic.html"
        icon = "image"
        label = "Image mosaic with feature card"


class ProfileBlock(blocks.StructBlock):
    photo = ImageBlock()
    name = blocks.CharBlock(max_length=80)
    role = blocks.CharBlock(max_length=80)
    bio = blocks.TextBlock(required=False, max_length=500)

    class Meta:
        label_format = "{name}"


class StaffBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120)
    profiles = blocks.ListBlock(ProfileBlock(), min_num=1)

    class Meta:
        template = "core/blocks/staff.html"
        icon = "group"
        label = "Staff or leadership profiles"


class PrincipalQuoteBlock(blocks.StructBlock):
    quote = blocks.TextBlock(max_length=400)
    name = blocks.CharBlock(max_length=80)
    title = blocks.CharBlock(max_length=80)
    portrait = ImageBlock()
    secondary_image = ImageBlock(required=False)
    signature = blocks.CharBlock(required=False, max_length=6, help_text="Initials shown in a signature style.")

    class Meta:
        template = "core/blocks/principal_quote.html"
        icon = "openquote"
        label = "Leader's message"


class TestimonialItemBlock(blocks.StructBlock):
    quote = blocks.TextBlock(max_length=500)
    name = blocks.CharBlock(max_length=80)
    detail = blocks.CharBlock(required=False, max_length=80, help_text="For example a programme or class year.")

    class Meta:
        label_format = "{name}"


class TestimonialsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120)
    items = blocks.ListBlock(TestimonialItemBlock(), min_num=1)

    class Meta:
        template = "core/blocks/testimonials.html"
        icon = "openquote"
        label = "Testimonials"


class StatItemBlock(blocks.StructBlock):
    value = blocks.CharBlock(max_length=20)
    label = blocks.CharBlock(max_length=60)

    class Meta:
        label_format = "{value} {label}"


class StatsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    stats = blocks.ListBlock(StatItemBlock(), min_num=1, max_num=6)

    class Meta:
        template = "core/blocks/stats.html"
        icon = "order"
        label = "Statistics"


class CallToActionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120)
    text = blocks.TextBlock(required=False, max_length=400)
    button = LinkBlock()
    tone = blocks.ChoiceBlock(choices=[("navy", "Navy"), ("gold", "Gold")], default="navy")

    class Meta:
        template = "core/blocks/call_to_action.html"
        icon = "pick"
        label = "Call to action"


class InfoCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=80)
    text = blocks.TextBlock(max_length=500)

    class Meta:
        label_format = "{title}"


class InfoCardsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    cards = blocks.ListBlock(InfoCardBlock(), min_num=1, max_num=8)

    class Meta:
        template = "core/blocks/info_cards.html"
        icon = "list-ul"
        label = "Text cards (values, requirements)"


class TimelineItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=40, help_text="A year, a date or a short label.")
    title = blocks.CharBlock(max_length=100)
    text = blocks.TextBlock(required=False, max_length=400)

    class Meta:
        label_format = "{label}: {title}"


class TimelineBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    numbered = blocks.BooleanBlock(
        required=False,
        label="Show as numbered steps",
        help_text="Use for a sequence such as an application process. Leave off for history or deadlines.",
    )
    items = blocks.ListBlock(TimelineItemBlock(), min_num=1)

    class Meta:
        template = "core/blocks/timeline.html"
        icon = "history"
        label = "Timeline or steps"


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(max_length=200)
    answer = blocks.RichTextBlock(features=RICH_FEATURES)

    class Meta:
        label_format = "{question}"


class FAQBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    items = blocks.ListBlock(FAQItemBlock(), min_num=1)

    class Meta:
        template = "core/blocks/faq.html"
        icon = "help"
        label = "Questions and answers"


class DownloadItemBlock(blocks.StructBlock):
    document = DocumentChooserBlock()
    title = blocks.CharBlock(required=False, max_length=120, help_text="Defaults to the document title.")
    description = blocks.CharBlock(required=False, max_length=200)

    class Meta:
        label_format = "{title}"


class DownloadsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120)
    items = blocks.ListBlock(DownloadItemBlock(), min_num=1)

    class Meta:
        template = "core/blocks/downloads.html"
        icon = "doc-empty"
        label = "Downloads"


class GalleryImageBlock(blocks.StructBlock):
    image = ImageBlock()
    caption = blocks.CharBlock(required=False, max_length=200)

    class Meta:
        label_format = "{caption}"


class GalleryBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=120)
    images = blocks.ListBlock(GalleryImageBlock(), min_num=1)

    class Meta:
        template = "core/blocks/gallery.html"
        icon = "image"
        label = "Image gallery"


class ContactDetailsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(default="Contact the school", max_length=120)

    class Meta:
        template = "core/blocks/contact_details.html"
        icon = "mail"
        label = "Contact details (from site settings)"
        help_text = "Shows the phone, email, addresses and office hours set in Settings > Site settings."


class NewsListingBlock(blocks.StructBlock):
    heading = blocks.CharBlock(default="News and announcements", max_length=120)
    count = blocks.IntegerBlock(default=3, min_value=1, max_value=6)

    class Meta:
        template = "core/blocks/news_listing.html"
        icon = "doc-full-inverse"
        label = "Latest news"

    def get_context(self, value, parent_context=None):
        from news.models import NewsArticlePage, NewsIndexPage

        context = super().get_context(value, parent_context)
        context["articles"] = (
            NewsArticlePage.objects.live().public()
            .select_related("cover_image")
            .prefetch_related("categories")
            .order_by("-date", "-first_published_at")[: value["count"]]
        )
        context["index_page"] = NewsIndexPage.objects.live().first()
        return context


class EventsListingBlock(blocks.StructBlock):
    heading = blocks.CharBlock(default="Upcoming events", max_length=120)
    count = blocks.IntegerBlock(default=3, min_value=1, max_value=6)

    class Meta:
        template = "core/blocks/events_listing.html"
        icon = "date"
        label = "Upcoming events"

    def get_context(self, value, parent_context=None):
        from events.models import EventsIndexPage, upcoming_events

        context = super().get_context(value, parent_context)
        context["events"] = upcoming_events()[: value["count"]]
        context["index_page"] = EventsIndexPage.objects.live().first()
        return context


# Blocks available on the home page and on general content pages.
SECTION_BLOCKS = [
    ("section_intro", SectionIntroBlock()),
    ("text", RichTextSectionBlock()),
    ("image_text", ImageTextBlock()),
    ("split_intro", SplitIntroBlock()),
    ("tiles", FeatureTilesBlock()),
    ("mosaic", FacilityMosaicBlock()),
    ("info_cards", InfoCardsBlock()),
    ("staff", StaffBlock()),
    ("leader_message", PrincipalQuoteBlock()),
    ("testimonials", TestimonialsBlock()),
    ("stats", StatsBlock()),
    ("timeline", TimelineBlock()),
    ("faq", FAQBlock()),
    ("downloads", DownloadsBlock()),
    ("gallery", GalleryBlock()),
    ("news", NewsListingBlock()),
    ("events", EventsListingBlock()),
    ("contact_details", ContactDetailsBlock()),
    ("cta", CallToActionBlock()),
]


class FAQCategoryBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100)
    items = blocks.ListBlock(FAQItemBlock(), min_num=1)

    class Meta:
        icon = "folder-open-inverse"
        label_format = "{title}"

# Smaller set for articles, events and similar detail pages.
_ARTICLE_KEYS = {"text", "image_text", "gallery", "downloads", "cta", "faq"}
ARTICLE_BLOCKS = [b for b in SECTION_BLOCKS if b[0] in _ARTICLE_KEYS]
