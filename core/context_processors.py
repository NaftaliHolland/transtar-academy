from wagtail.models import Site

from .models import NavigationSettings, SiteSettings


def site(request):
    """Expose global settings to every template as ``site_settings`` and ``nav_settings``."""
    if Site.find_for_request(request) is None:
        return {}
    return {
        "site_settings": SiteSettings.for_request(request),
        "nav_settings": NavigationSettings.for_request(request),
    }
