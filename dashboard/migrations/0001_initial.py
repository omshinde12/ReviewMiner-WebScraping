# Generated by Django 5.0.7 on 2025-02-03 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255)),
                ('review_text', models.TextField()),
                ('rating', models.DecimalField(decimal_places=1, max_digits=3)),
                ('location', models.CharField(max_length=255)),
                ('review_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
