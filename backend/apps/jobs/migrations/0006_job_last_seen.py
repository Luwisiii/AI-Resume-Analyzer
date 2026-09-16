import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0005_job_company_job_location_job_url_job_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="last_seen",
            # Existing rows are treated as seen now; the next fetch corrects any
            # that have actually closed by simply not touching them again.
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
