from django.core.management.base import BaseCommand

from apps.jobs.tasks import fetch_jooble_jobs, fetch_remotive_jobs, refresh_jobs

SOURCES = ["remotive", "jooble"]


class Command(BaseCommand):
    help = "Fetch real job postings from the web into the Job table."

    def add_arguments(self, parser):
        parser.add_argument("--source", choices=SOURCES + ["all"], default="all")
        parser.add_argument("--search", default="", help="Keyword filter, e.g. 'python'")
        parser.add_argument("--location", default="Philippines", help="Jooble only")
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        source, search, location, limit = (
            options["source"], options["search"], options["location"], options["limit"]
        )

        # A full refresh also prunes postings that have stopped being listed. A
        # single-source run does not: the other source's postings would all look
        # stale to it and get deleted.
        if source == "all":
            for name, result in refresh_jobs(
                search=search, location=location, limit=limit
            ).items():
                self.stdout.write(self.style.SUCCESS(f"{name}: {result}"))
            return

        calls = {
            "remotive": lambda: fetch_remotive_jobs(search=search or None, limit=limit),
            "jooble": lambda: fetch_jooble_jobs(search=search, location=location, limit=limit),
        }
        try:
            self.stdout.write(self.style.SUCCESS(f"{source}: {calls[source]()}"))
        except RuntimeError as exc:
            self.stderr.write(self.style.WARNING(f"{source} skipped: {exc}"))
