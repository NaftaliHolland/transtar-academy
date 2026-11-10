from datetime import timedelta

from django.utils import timezone

from core.tests.test_site import SeededSiteTestCase
from events.models import EventPage, EventsIndexPage, past_events, upcoming_events


class EventTests(SeededSiteTestCase):
    def test_upcoming_and_past_are_separated(self):
        self.assertEqual(upcoming_events().count(), 3)
        self.assertEqual([e.title for e in past_events()], ["Sample past event: sports day"])

    def test_upcoming_ordered_soonest_first(self):
        starts = [e.start_datetime for e in upcoming_events()]
        self.assertEqual(starts, sorted(starts))

    def test_event_without_end_uses_start(self):
        index = EventsIndexPage.objects.get()
        event = EventPage(title="Today later", slug="later", start_datetime=timezone.now() + timedelta(hours=1), summary="x")
        index.add_child(instance=event)
        event.save_revision().publish()
        self.assertIn(event.pk, [e.pk for e in upcoming_events()])
        self.assertTrue(event.is_upcoming)

    def test_listing_toggle(self):
        index = EventsIndexPage.objects.get()
        self.assertContains(self.client.get(index.url), "Sample open house")
        past = self.client.get(index.url, {"when": "past"})
        self.assertContains(past, "Sample past event")
        self.assertNotContains(past, "Sample open house")

    def test_past_event_page_says_ended(self):
        page = EventPage.objects.get(slug="sample-event-4")
        self.assertContains(self.client.get(page.url), "This event has ended")
