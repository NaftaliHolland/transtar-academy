from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from wagtail.models import Page


def search(request):
    query = request.GET.get("query", "").strip()
    results = Page.objects.live().public().search(query) if query else Page.objects.none()
    paginator = Paginator(results, 10)
    return TemplateResponse(
        request,
        "search/search.html",
        {"search_query": query, "search_results": paginator.get_page(request.GET.get("page"))},
    )
