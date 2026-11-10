from django.contrib.auth import get_user_model
from wagtail.models import Page

from core.tests.test_site import SeededSiteTestCase


class AdminSmokeTests(SeededSiteTestCase):
    """The editing screens for every page type and setting must load."""

    def test_editor_screens_load(self):
        get_user_model().objects.create_superuser("admin", "a@example.org", "pw-for-tests-123")
        self.client.login(username="admin", password="pw-for-tests-123")
        for page in Page.objects.exclude(depth=1):
            response = self.client.get(f"/admin/pages/{page.pk}/edit/")
            self.assertEqual(response.status_code, 200, f"edit {page.specific_class.__name__} failed")
        for url in ["/admin/settings/core/sitesettings/", "/admin/settings/core/navigationsettings/",
                    "/admin/snippets/contact/contactsubmission/", "/admin/snippets/news/newscategory/"]:
            self.assertEqual(self.client.get(url, follow=True).status_code, 200, url)
