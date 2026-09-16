from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_job_industry"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="company",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="job",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="job",
            name="source",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="job",
            name="url",
            field=models.URLField(blank=True, max_length=500, null=True, unique=True),
        ),
    ]
