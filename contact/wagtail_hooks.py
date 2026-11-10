from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import ContactSubmission


class ContactSubmissionViewSet(SnippetViewSet):
    model = ContactSubmission
    icon = "mail"
    menu_label = "Enquiries"
    menu_name = "enquiries"
    add_to_admin_menu = True
    menu_order = 300
    inspect_view_enabled = True
    list_display = ["name", "email", "category", "created_at", "handled"]
    list_filter = ["handled", "category"]
    list_export = ["name", "email", "phone", "category", "message", "created_at", "handled"]
    search_fields = ["name", "email", "message"]


register_snippet(ContactSubmissionViewSet)
