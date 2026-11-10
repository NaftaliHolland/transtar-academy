from django import template
from django.utils.html import strip_tags

register = template.Library()

SOCIAL_LABELS = {
    "facebook": "Facebook",
    "twitter": "X (Twitter)",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "youtube": "YouTube",
}


@register.simple_tag(takes_context=True)
def is_current(context, href):
    """True when ``href`` is the current page or one of its ancestors in the URL structure."""
    request = context.get("request")
    if not request or not href or href.startswith("http"):
        return False
    if href == "/":
        return request.path == "/"
    return request.path == href or request.path.startswith(href)


@register.simple_tag
def social_label(platform):
    return SOCIAL_LABELS.get(platform, platform.title())


@register.filter
def plain(value):
    return strip_tags(str(value or ""))


@register.inclusion_tag("includes/seo.html", takes_context=True)
def seo_meta(context):
    request = context.get("request")
    page = context.get("page")
    settings_ = context.get("site_settings")
    title = description = image = None
    if page is not None and hasattr(page, "get_meta_title"):
        title = page.get_meta_title()
        description = page.get_meta_description()
        image = page.get_meta_image()
    elif page is not None:
        title = getattr(page, "title", None)
    if not description and settings_:
        description = settings_.default_meta_description
    if not image and settings_:
        image = settings_.default_social_image
    canonical = request.build_absolute_uri(request.path) if request else ""
    return {
        "request": request,
        "meta_title": title or context.get("meta_title") or "",
        "meta_description": description or "",
        "meta_image": image,
        "canonical": canonical,
        "site_settings": settings_,
        "og_type": context.get("og_type", "website"),
    }


@register.simple_tag(takes_context=True)
def page_url(context, number):
    """Current URL with ?page=<number>, keeping any other query parameters (filters)."""
    request = context["request"]
    params = request.GET.copy()
    params["page"] = number
    return "?" + params.urlencode()


@register.simple_tag(takes_context=True)
def filter_url(context, **kwargs):
    """Current path with the given query parameters replaced; empty values remove a parameter."""
    request = context["request"]
    params = request.GET.copy()
    params.pop("page", None)
    for key, value in kwargs.items():
        if value:
            params[key] = value
        else:
            params.pop(key, None)
    query = params.urlencode()
    return request.path + ("?" + query if query else "")


@register.filter
def json_script_safe(value):
    """Encode plain text as a JSON string that is safe inside an inline <script> block."""
    import json

    from django.utils.safestring import mark_safe

    text = strip_tags(str(value or ""))
    encoded = json.dumps(text).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(encoded)
