from core.tests.test_site import SeededSiteTestCase
from news.models import NewsArticlePage, NewsCategory, NewsIndexPage


class NewsTests(SeededSiteTestCase):
    def setUp(self):
        self.index = NewsIndexPage.objects.get()

    def test_featured_article_leads_listing(self):
        response = self.client.get(self.index.url)
        self.assertEqual(response.context["featured"].slug, "sample-news-1")

    def test_category_filter(self):
        response = self.client.get(self.index.url, {"category": "campus-news"})
        titles = [a.title for a in response.context["page_obj"]]
        self.assertEqual(len(titles), 2)
        self.assertIsNone(response.context["featured"])

    def test_tag_filter(self):
        response = self.client.get(self.index.url, {"tag": "sample"})
        self.assertEqual(len(response.context["page_obj"]), 3)

    def test_articles_newest_first_and_paginated(self):
        response = self.client.get(self.index.url, {"page": "999"})  # clamps to last page
        self.assertEqual(response.status_code, 200)
        dates = [a.date for a in self.index.get_articles()]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_draft_articles_are_hidden(self):
        article = NewsArticlePage.objects.get(slug="sample-news-2")
        article.unpublish()
        self.assertNotContains(self.client.get(self.index.url), "library update")

    def test_listing_query_count_is_bounded(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.index.url)
        self.assertLess(len(ctx), 45)
