from django import forms
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from core.blocks import ARTICLE_BLOCKS
from core.models import BasePage


@register_snippet
class NewsCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)

    panels = [FieldPanel("name"), FieldPanel("slug")]

    class Meta:
        verbose_name = "news category"
        verbose_name_plural = "news categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class NewsPageTag(TaggedItemBase):
    content_object = ParentalKey("news.NewsArticlePage", related_name="tagged_items", on_delete=models.CASCADE)


class NewsIndexPage(BasePage):
    intro = models.TextField(blank=True, max_length=400)

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage", "core.StandardPage"]
    subpage_types = ["news.NewsArticlePage"]
    paginate_by = 9

    class Meta:
        verbose_name = "news listing page"

    def get_articles(self):
        return (
            NewsArticlePage.objects.child_of(self).live().public()
            .select_related("cover_image")
            .prefetch_related("categories")
            .order_by("-date", "-first_published_at")
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        articles = self.get_articles()
        category = request.GET.get("category", "").strip()
        tag = request.GET.get("tag", "").strip()
        active_category = None
        if category:
            articles = articles.filter(categories__slug=category)
            active_category = NewsCategory.objects.filter(slug=category).first()
        if tag:
            articles = articles.filter(tags__slug=tag)
        featured = None
        if not (category or tag) and request.GET.get("page", "1") in ("", "1"):
            featured = articles.filter(featured=True).first()
            if featured:
                articles = articles.exclude(pk=featured.pk)
        page_obj = Paginator(articles, self.paginate_by).get_page(request.GET.get("page"))
        context.update(
            featured=featured,
            page_obj=page_obj,
            categories=NewsCategory.objects.all(),
            active_category=active_category,
            active_tag=tag,
        )
        return context


class NewsArticlePage(BasePage):
    seo_description_field = "intro"

    date = models.DateField(default=timezone.localdate, help_text="Publication date shown on the article.")
    author_name = models.CharField(max_length=100, blank=True)
    intro = models.TextField(max_length=400, help_text="Short summary shown in listings.")
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    body = StreamField(ARTICLE_BLOCKS, blank=True)
    categories = ParentalManyToManyField(NewsCategory, blank=True)
    tags = ClusterTaggableManager(through=NewsPageTag, blank=True)
    featured = models.BooleanField(default=False, help_text="Featured articles lead the news listing.")

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("date"), FieldPanel("author_name"), FieldPanel("featured")], heading="Details"),
        FieldPanel("intro"),
        FieldPanel("cover_image"),
        FieldPanel("body"),
        MultiFieldPanel([FieldPanel("categories", widget=forms.CheckboxSelectMultiple), FieldPanel("tags")], heading="Categories and tags"),
    ]
    search_fields = Page.search_fields + [index.SearchField("intro"), index.SearchField("body")]

    parent_page_types = ["news.NewsIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "news article"

    def get_meta_image(self):
        return self.social_image or self.cover_image
