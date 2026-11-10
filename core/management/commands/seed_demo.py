"""Create clearly-labelled demonstration content so the site looks complete on first run.

Everything here is placeholder text and generated placeholder images. Replace it through the Wagtail admin.
Run ``python manage.py seed_demo`` once on a fresh database, or add ``--reset`` to rebuild the demo pages.
"""
import io
import json
import uuid
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image as PILImage, ImageDraw, ImageFont
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Site

from contact.models import ContactPage
from core.models import FAQPage, NavigationSettings, SiteSettings, StandardPage
from events.models import EventPage, EventsIndexPage
from gallery.models import AlbumImage, AlbumPage, GalleryIndexPage
from home.models import HomePage
from news.models import NewsArticlePage, NewsCategory, NewsIndexPage

NAVY, PERIWINKLE, STEEL, GOLD, MIST = (29, 21, 124), (74, 103, 184), (60, 84, 148), (251, 185, 17), (227, 235, 255)
DEMO = "Demonstration content: replace this in the Wagtail admin."


def p(text):
    return f"<p>{text}</p>"


def lst(items):
    items = [i["value"] if isinstance(i, dict) and i.get("type") == "item" and "value" in i else i for i in items]
    return [{"type": "item", "value": v, "id": str(uuid.uuid4())} for v in items]


def link(page=None, label="", url=""):
    return {"label": label, "page": page.pk if page else None, "url": url}


class Command(BaseCommand):
    help = "Create demonstration pages, navigation and placeholder images."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing child pages of the home page first.")

    # ------------------------------------------------------------------ helpers
    def image(self, key, label, size, color):
        existing = Image.objects.filter(title=f"Placeholder: {label}").first()
        if existing:
            return existing
        w, h = size
        canvas = PILImage.new("RGB", size, color)
        draw = ImageDraw.Draw(canvas)
        band = max(w // 7, 60)
        lighter = tuple(min(255, c + 22) for c in color)
        for x in range(-h, w, band * 2):
            draw.polygon([(x, h), (x + h // 2, 0), (x + h // 2 + band, 0), (x + band, h)], fill=lighter)
        font = ImageFont.load_default(size=max(18, w // 22))
        text = f"Placeholder\n{label}"
        box = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        draw.multiline_text(((w - box[2]) / 2, (h - box[3]) / 2), text, font=font, fill=(255, 255, 255), align="center")
        buf = io.BytesIO()
        canvas.save(buf, "JPEG", quality=82)
        return Image.objects.create(
            title=f"Placeholder: {label}",
            description=f"Placeholder image: {label}",
            file=ContentFile(buf.getvalue(), name=f"placeholder-{key}.jpg"),
            width=w,
            height=h,
        )

    def img(self, image, alt=None):
        return {"image": image.pk, "alt_text": alt or image.description, "decorative": False}

    def child(self, parent, model, title, slug, **fields):
        page = model.objects.filter(slug=slug, path__startswith=parent.path).first()
        if page:
            return page
        page = model(title=title, slug=slug, **fields)
        parent.add_child(instance=page)
        return page

    def publish(self, page):
        page.save_revision().publish()

    def document(self, title, filename):
        existing = Document.objects.filter(title=title).first()
        if existing:
            return existing
        body = f"{title}\n\nThis is a placeholder file. Replace it with the school's real document in the Wagtail admin.\n"
        return Document.objects.create(title=title, file=ContentFile(body.encode(), name=filename))

    # ------------------------------------------------------------------ main
    def handle(self, *args, **options):
        site = Site.objects.get(is_default_site=True)
        home = HomePage.objects.get(pk=site.root_page_id)
        if options["reset"]:
            for child in home.get_children():
                child.delete()
            home = HomePage.objects.get(pk=home.pk)
        elif home.get_children().exists():
            self.stdout.write("Demo content already exists. Use --reset to rebuild it.")
            return

        pic = {
            "hero": self.image("hero", "campus", (1920, 1080), NAVY),
            "t1": self.image("t1", "students collaborating", (800, 480), STEEL),
            "t2": self.image("t2", "students learning together", (800, 480), PERIWINKLE),
            "t3": self.image("t3", "graduating students", (800, 480), NAVY),
            "c1": self.image("c1", "health and sciences", (1000, 600), NAVY),
            "c2": self.image("c2", "business academics", (1000, 600), PERIWINKLE),
            "c3": self.image("c3", "library", (1000, 600), STEEL),
            "f1": self.image("f1", "library", (1000, 420), STEEL),
            "f2": self.image("f2", "computer lab", (1000, 420), NAVY),
            "f3": self.image("f3", "school building", (1000, 420), PERIWINKLE),
            "f4": self.image("f4", "collaborative classroom", (1000, 420), STEEL),
            "p1": self.image("p1", "staff portrait 1", (600, 600), NAVY),
            "p2": self.image("p2", "staff portrait 2", (600, 600), PERIWINKLE),
            "p3": self.image("p3", "staff portrait 3", (600, 600), NAVY),
            "p4": self.image("p4", "staff portrait 4", (600, 600), PERIWINKLE),
            "p5": self.image("p5", "staff portrait 5", (600, 600), NAVY),
            "lead": self.image("lead", "principal", (720, 1040), STEEL),
            "lead2": self.image("lead2", "principal on campus", (532, 330), PERIWINKLE),
            "n1": self.image("n1", "news one", (1000, 640), NAVY),
            "n2": self.image("n2", "news two", (1000, 640), STEEL),
            "n3": self.image("n3", "news three", (1000, 640), PERIWINKLE),
            "e1": self.image("e1", "event one", (1000, 640), STEEL),
            "e2": self.image("e2", "event two", (1000, 640), NAVY),
            "e3": self.image("e3", "event three", (1000, 640), PERIWINKLE),
        }

        # ---- page tree (empty shells first so links can point at them)
        about = self.child(home, StandardPage, "About us", "about-us", intro=f"{DEMO} Introduce the school's story and identity.")
        leadership = self.child(about, StandardPage, "Leadership", "leadership", intro=DEMO)
        academics = self.child(home, StandardPage, "Academics", "academics", intro=f"{DEMO} Describe the academic programme.")
        admissions = self.child(home, StandardPage, "Admissions", "admissions", intro=f"{DEMO} Explain how families apply.")
        faq = self.child(home, FAQPage, "Frequently asked questions", "faq", intro=DEMO)
        student_life = self.child(home, StandardPage, "Student life", "student-life", intro=f"{DEMO} Clubs, sport and student support.")
        facilities = self.child(home, StandardPage, "Facilities", "facilities", intro=f"{DEMO} Show the campus and what it offers.")
        news = self.child(home, NewsIndexPage, "News and announcements", "news", intro=DEMO)
        events = self.child(home, EventsIndexPage, "Events", "events", intro=DEMO)
        gallery = self.child(home, GalleryIndexPage, "Gallery", "gallery", intro=DEMO)
        policies = self.child(home, StandardPage, "Policies and downloads", "policies", intro=f"{DEMO} Policies, forms and the prospectus.")
        privacy = self.child(policies, StandardPage, "Privacy policy", "privacy-policy", intro=DEMO)
        contact = self.child(home, ContactPage, "Contact us", "contact", intro=f"{DEMO} Questions about the school? Send us a message.")

        form_doc = self.document("Application form (placeholder)", "application-form.txt")
        prospectus = self.document("School prospectus (placeholder)", "prospectus.txt")
        calendar = self.document("Academic calendar (placeholder)", "academic-calendar.txt")
        policy_doc = self.document("Code of conduct (placeholder)", "code-of-conduct.txt")

        def dl(title, doc, text=""):
            return {"document": doc.pk, "title": title, "description": text}

        # ---- global settings
        settings_ = SiteSettings.for_site(site)
        settings_.school_name = "Glory High School"
        settings_.tagline = "High school redefined for success"
        settings_.phone = "+000 000 000 000"
        settings_.email = "info@example.org"
        settings_.admissions_email = "admissions@example.org"
        settings_.physical_address = "Physical address placeholder\nTown, Country"
        settings_.postal_address = "P.O. Box 000\nTown, Country"
        settings_.office_hours = "Monday to Friday: 8:00 to 16:30\nSaturday and Sunday: closed"
        settings_.footer_text = "Excellence meets innovation."
        settings_.copyright_text = "All rights reserved."
        settings_.cta_text = "Apply now"
        settings_.cta_page = admissions
        settings_.default_meta_description = "Glory High School: high school redefined for success."
        settings_.default_social_image = pic["hero"]
        settings_.social_links = json.dumps(
            [{"type": "link", "value": {"platform": k, "url": u}} for k, u in [
                ("facebook", "https://www.facebook.com/"), ("twitter", "https://x.com/"),
                ("instagram", "https://www.instagram.com/"), ("linkedin", "https://www.linkedin.com/"),
                ("youtube", "https://www.youtube.com/")]]
        )
        settings_.save()

        nav = NavigationSettings.for_site(site)
        item = lambda label, page=None, children=(): {"type": "item", "value": {**link(page, label), "children": lst(children)}}  # noqa: E731
        nav.header_menu = json.dumps([
            item("Academics", academics),
            item("Admissions", admissions, [link(admissions, "How to apply"), link(faq)]),
            item("About us", about, [link(about), link(leadership), link(policies)]),
            item("Campus life", None, [link(student_life), link(facilities), link(gallery), link(news), link(events)]),
            item("Contact", contact),
        ])
        nav.utility_menu = json.dumps([{"type": "link", "value": link(news)}, {"type": "link", "value": link(events)}, {"type": "link", "value": link(faq)}])
        nav.footer_columns = json.dumps([
            {"type": "column", "value": {"title": "Explore", "links": lst([link(academics), link(admissions), link(about)])}},
            {"type": "column", "value": {"title": "Campus", "links": lst([link(student_life), link(facilities), link(gallery)])}},
            {"type": "column", "value": {"title": "Information", "links": lst([link(faq), link(policies), link(privacy)])}},
        ])
        nav.save()

        # ---- news, events, gallery
        announcements, _ = NewsCategory.objects.get_or_create(slug="announcements", defaults={"name": "Announcements"})
        campus, _ = NewsCategory.objects.get_or_create(slug="campus-news", defaults={"name": "Campus news"})
        today = timezone.localdate()
        for i, (title, cat, image, featured) in enumerate([
            ("Sample news article: term begins", announcements, pic["n1"], True),
            ("Sample news article: library update", campus, pic["n2"], False),
            ("Sample news article: student showcase", campus, pic["n3"], False),
        ]):
            art = self.child(news, NewsArticlePage, title, f"sample-news-{i + 1}", date=today - timedelta(days=i * 6),
                             intro=f"{DEMO} A short summary appears in listings.", cover_image=image, featured=featured,
                             author_name="School office")
            art.body = json.dumps([{"type": "text", "value": {"heading": "", "body": p(f"{DEMO} Write the full article here."), "tone": "white"}}])
            art.categories.add(cat)
            art.tags.add("sample")
            self.publish(art)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        for i, (title, delta, image) in enumerate([
            ("Sample open house", 14, pic["e1"]), ("Sample student showcase", 30, pic["e2"]),
            ("Sample parents' evening", 45, pic["e3"]), ("Sample past event: sports day", -20, pic["e1"]),
        ]):
            start = now + timedelta(days=delta, hours=2)
            ev = self.child(events, EventPage, title, f"sample-event-{i + 1}", start_datetime=start,
                            end_datetime=start + timedelta(hours=3), location="School campus (placeholder)",
                            summary=f"{DEMO} Say what happens and who should attend.", image=image, featured=i == 0)
            ev.body = json.dumps([{"type": "text", "value": {"heading": "", "body": p(DEMO), "tone": "white"}}])
            self.publish(ev)

        for a, (title, keys) in enumerate([("Sample album: campus life", ["c1", "c2", "c3", "t1"]), ("Sample album: facilities", ["f1", "f2", "f3", "f4"])]):
            album = self.child(gallery, AlbumPage, title, f"sample-album-{a + 1}", intro=DEMO, date=today - timedelta(days=a * 20))
            if not album.gallery_images.exists():
                for k in keys:
                    AlbumImage.objects.create(page=album, image=pic[k], caption=f"Placeholder photo ({k})")
            self.publish(album)

        # ---- content pages
        tile = lambda key, title, text="", page=None: {"type": "item", "value": {"image": self.img(pic[key]), "title": title, "description": text, "link": link(page)}}  # noqa: E731
        profile = lambda key, name, role: {"type": "item", "value": {"photo": self.img(pic[key], name), "name": name, "role": role, "bio": ""}}  # noqa: E731
        card = lambda t, x: {"type": "item", "value": {"title": t, "text": x}}  # noqa: E731
        block = lambda kind, value: {"type": kind, "value": value}  # noqa: E731
        text_block = lambda heading, body, tone="white": block("text", {"heading": heading, "body": body, "tone": tone})  # noqa: E731

        home.hero_image = pic["hero"]
        home.hero_heading = "Unlock Your\nFuture Success"
        home.hero_tagline = "High School Redefined for Success"
        home.hero_tiles = json.dumps([
            {"type": "tile", "value": {"image": self.img(pic["t1"]), "title": "Career-Oriented Curriculum", "link": link(academics)}},
            {"type": "tile", "value": {"image": self.img(pic["t2"]), "title": "Skills for Professional Success", "link": link(about)}},
            {"type": "tile", "value": {"image": self.img(pic["t3"]), "title": "Supportive Environment", "link": link(student_life)}},
        ])
        home.body = json.dumps([
            block("split_intro", {
                "items": lst([
                    {"icon": None, "heading": "Featured Programs", "text": "Discover our acclaimed programs designed to unlock your child's potential. From advanced academic courses to a rich tapestry of extracurricular activities, School provides a holistic education that goes beyond the classroom."},
                    {"icon": None, "heading": "Upcoming Events", "text": "Stay connected with our vibrant community through upcoming events. Join us for open houses, student showcases, and interactive webinars to get a firsthand look at the dynamic learning experiences School offers."},
                ]),
                "panel_heading": "Welcome",
                "panel_text": "Welcome to our school, where excellence meets innovation. Our commitment to fostering academic achievement, personal growth, and community engagement sets us apart. Explore a transformative educational journey that prepares students for a future of limitless possibilities.",
                "panel_link": link(about, "Read more about us"),
            }),
            block("tiles", {"heading": "Our Courses", "tiles": lst([
                tile("c1", "Health and Sciences", "Explore a future-focused curriculum, experienced educators, and practical learning designed to help every student thrive.", academics)["value"],
                tile("c2", "Business Academics", "Explore a future-focused curriculum, experienced educators, and practical learning designed to help every student thrive.", academics)["value"],
                tile("c3", "History", "Explore a future-focused curriculum, experienced educators, and practical learning designed to help every student thrive.", academics)["value"],
            ])}),
            block("mosaic", {"heading": "Our Facilities", "text": "Immerse yourself in a conducive learning environment with our top-notch facilities. State-of-the-art laboratories, extensive libraries, and modern classrooms create a setting where curiosity and exploration flourish.",
                             "images": lst([self.img(pic["f1"], "School library"), self.img(pic["f2"], "Computer lab"), self.img(pic["f3"], "School building"), self.img(pic["f4"], "Collaborative classroom")])}),
            block("news", {"heading": "News and announcements", "count": 3}),
            block("events", {"heading": "Upcoming events", "count": 3}),
            block("staff", {"heading": "Meet our team of dedicated educators", "profiles": lst([
                profile("p1", "Anita Lee", "Art Director")["value"], profile("p2", "Bruce Smith", "Art Director")["value"],
                profile("p3", "Jack Nicholson", "Art Director")["value"], profile("p4", "Calvin", "Art Director")["value"],
                profile("p5", "Anita Lee", "Art Director")["value"]])}),
            block("leader_message", {"quote": "At our School, we aim to empower students with the skills, knowledge, and values needed for success in a global context.",
                                     "name": "Joseph Panda", "title": "Principal", "portrait": self.img(pic["lead"], "Joseph Panda, principal"),
                                     "secondary_image": self.img(pic["lead2"], "The principal speaking on campus"), "signature": "JP"}),
            block("testimonials", {"heading": "What Our Students Say", "items": lst([
                {"quote": "We provide students with timely and tailored support & services. We offer culturally sensitive and engaged teach learning and assessment needs.", "name": n, "detail": d}
                for n, d in [("Steve Martin", "Humanities"), ("Geoffrey", "Arts and commerce"), ("Joe Shelf", "Humanities")]])}),
        ])
        self.publish(home)

        about.body = json.dumps([
            text_block("Our story", p(f"{DEMO} Tell visitors how the school began and what it stands for.")),
            block("info_cards", {"heading": "Vision, mission and values", "cards": lst([
                card("Vision", "Replace with the school's vision."), card("Mission", "Replace with the school's mission."),
                card("Core values", "Replace with the values the school lives by.")])}),
            block("cta", {"heading": "Meet the leadership team", "text": "", "button": link(leadership), "tone": "navy"}),
        ])
        leadership.body = json.dumps([block("staff", {"heading": "School leadership", "profiles": lst([profile("p1", "Name placeholder", "Role placeholder")["value"], profile("p2", "Name placeholder", "Role placeholder")["value"]])})])
        academics.body = json.dumps([
            text_block("Our approach to learning", p(f"{DEMO} Explain the curriculum and teaching philosophy.")),
            block("tiles", {"heading": "Learning areas", "tiles": lst([tile("c1", "Health and Sciences", "Describe this learning area.")["value"], tile("c2", "Business Academics", "Describe this learning area.")["value"], tile("c3", "History", "Describe this learning area.")["value"]])}),
            block("downloads", {"heading": "Academic documents", "items": lst([dl("Academic calendar", calendar, "Term dates and key academic events.")])}),
        ])
        admissions.body = json.dumps([
            text_block("Admissions overview", p(f"{DEMO} Explain who can apply and what makes the school a good fit.")),
            block("info_cards", {"heading": "Admission requirements", "cards": lst([card("Requirement one", "Describe what applicants need."), card("Requirement two", "Describe what applicants need."), card("Requirement three", "Describe what applicants need.")])}),
            block("timeline", {"heading": "How to apply", "numbered": True, "items": lst([
                {"label": "", "title": "Make an enquiry", "text": "Describe the first step."}, {"label": "", "title": "Submit the application", "text": "Describe the second step."},
                {"label": "", "title": "Receive a decision", "text": "Describe the final step."}])}),
            block("timeline", {"heading": "Important dates", "numbered": False, "items": lst([{"label": "To be confirmed", "title": "Applications open", "text": ""}, {"label": "To be confirmed", "title": "Applications close", "text": ""}])}),
            block("downloads", {"heading": "Forms and documents", "items": lst([dl("Application form", form_doc, "Download, complete and return to the admissions office."), dl("School prospectus", prospectus)])}),
            block("cta", {"heading": "Ready to talk to us?", "text": "Send an admissions enquiry and we will reply.", "button": link(contact, "Make an enquiry", ""), "tone": "gold"}),
        ])
        faq.categories = json.dumps([
            {"type": "category", "value": {"title": "Admissions", "items": lst([{"question": "How do I apply?", "answer": p(DEMO)}, {"question": "When do applications close?", "answer": p(DEMO)}])}},
            {"type": "category", "value": {"title": "School life", "items": lst([{"question": "What clubs are available?", "answer": p(DEMO)}])}},
        ])
        student_life.body = json.dumps([block("info_cards", {"heading": "Beyond the classroom", "cards": lst([
            card("Clubs and societies", "Describe the clubs students can join."), card("Sports", "Describe sports and fitness activities."),
            card("Student leadership", "Describe prefects and student councils."), card("Co-curricular programmes", "Describe music, drama and other programmes."),
            card("Student welfare", "Describe counselling and support services.")])})])
        facilities.body = json.dumps([
            block("image_text", {"image": self.img(pic["f1"], "School library"), "heading": "Library", "text": p(DEMO), "button": link(), "image_position": "left", "tone": "white"}),
            block("image_text", {"image": self.img(pic["f2"], "Computer lab"), "heading": "Computer lab", "text": p(DEMO), "button": link(), "image_position": "right", "tone": "mist"}),
            block("image_text", {"image": self.img(pic["f4"], "Collaborative classroom"), "heading": "Classrooms", "text": p(DEMO), "button": link(), "image_position": "left", "tone": "white"}),
        ])
        policies.body = json.dumps([block("downloads", {"heading": "Policies and documents", "items": lst([dl("Code of conduct", policy_doc), dl("School prospectus", prospectus), dl("Application form", form_doc)])}),
                                    block("cta", {"heading": "Privacy policy", "text": "How the school handles personal information.", "button": link(privacy), "tone": "navy"})])
        privacy.body = json.dumps([text_block("", p("Replace this placeholder with the school's privacy policy, written or reviewed by a qualified adviser."))])
        contact.body = json.dumps([])

        for page in [about, leadership, academics, admissions, faq, student_life, facilities, news, events, gallery, policies, privacy, contact]:
            self.publish(page)
        self.stdout.write(self.style.SUCCESS("Demonstration content created."))
