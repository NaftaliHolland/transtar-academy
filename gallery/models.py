from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable, Page
from wagtail.search import index

from core.models import BasePage


class GalleryIndexPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = ["gallery.AlbumPage"]
    paginate_by = 12

    class Meta:
        verbose_name = "gallery page"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        albums = (
            AlbumPage.objects.child_of(self).live().public()
            .select_related("cover_image")
            .prefetch_related("gallery_images__image")
            .order_by("-date", "-first_published_at")
        )
        context["page_obj"] = Paginator(albums, self.paginate_by).get_page(request.GET.get("page"))
        return context


class AlbumPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)
    date = models.DateField(default=timezone.localdate)
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Optional. Defaults to the first image in the album.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("date"), FieldPanel("cover_image")], heading="Album"),
        FieldPanel("intro"),
        InlinePanel("gallery_images", label="Images", min_num=1),
    ]
    search_fields = Page.search_fields + [index.SearchField("intro")]

    parent_page_types = ["gallery.GalleryIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "gallery album"

    @property
    def cover(self):
        if self.cover_image_id:
            return self.cover_image
        first = next(iter(self.gallery_images.all()), None)
        return first.image if first else None

    def get_meta_image(self):
        return self.social_image or self.cover


class AlbumImage(Orderable):
    page = ParentalKey(AlbumPage, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(max_length=200, blank=True)

    panels = [FieldPanel("image"), FieldPanel("caption")]
