from django.core.management import call_command
from django.test import TestCase
from wagtail.blocks import StructBlockValidationError
from wagtail.models import Page

from core.blocks import LinkBlock, MenuItemBlock
from core.models import NavigationSettings, StandardPage


class SeededSiteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)


class PageRenderingTests(SeededSiteTestCase):
    def test_every_live_page_renders(self):
        pages = Page.objects.live().exclude(depth=1)
        self.assertGreater(pages.count(), 15)
        for page in pages:
            response = self.client.get(page.url)
            self.assertEqual(response.status_code, 200, f"{page.url} failed")

    def test_home_has_hero_sections_from_streamfield(self):
        html = self.client.get("/").content.decode()
        for text in ["Unlock Your", "Our Courses", "Our Facilities", "What Our Students Say", "Sample news article"]:
            self.assertIn(text, html)

    def test_navigation_comes_from_settings(self):
        html = self.client.get("/").content.decode()
        self.assertIn('aria-label="Main navigation"', html)
        self.assertIn("Academics", html)
        self.assertIn("Show Campus life submenu", html)

    def test_unknown_url_is_404(self):
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)

    def test_robots_and_sitemap(self):
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Disallow: /admin/")
        self.assertContains(robots, "sitemap.xml")
        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertContains(sitemap, "/academics/")

    def test_seo_tags_and_canonical(self):
        html = self.client.get("/academics/").content.decode()
        self.assertIn('rel="canonical"', html)
        self.assertIn('property="og:title"', html)
        self.assertIn("<title>Academics | Glory High School</title>", html)

    def test_editing_navigation_changes_output(self):
        nav = NavigationSettings.objects.get()
        nav.header_menu = []
        nav.save()
        html = self.client.get("/").content.decode()
        self.assertNotIn("Show Campus life submenu", html)

    def test_search(self):
        response = self.client.get("/search/", {"query": "Academics"})
        self.assertContains(response, "Academics")

    def test_standard_page_hierarchy(self):
        about = StandardPage.objects.get(slug="about-us")
        self.assertTrue(about.get_children().filter(slug="leadership").exists())


class LinkBlockTests(TestCase):
    def test_label_without_target_is_invalid(self):
        block = LinkBlock()
        with self.assertRaises(StructBlockValidationError):
            block.clean(block.to_python({"label": "Orphan", "page": None, "url": ""}))

    def test_menu_item_may_be_label_with_children(self):
        block = MenuItemBlock()
        value = block.to_python(
            {"label": "More", "page": None, "url": "", "children": [{"type": "item", "value": {"label": "Ext", "page": None, "url": "https://example.org"}, "id": "6d30bf9c-7468-49dd-a5cf-27f3f04c73fe"}]}
        )
        block.clean(value)

    def test_menu_item_without_link_or_children_is_invalid(self):
        block = MenuItemBlock()
        with self.assertRaises(StructBlockValidationError):
            block.clean(block.to_python({"label": "Empty", "page": None, "url": "", "children": []}))
