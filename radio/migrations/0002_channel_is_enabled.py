# Generated by Django 3.2.5 on 2021-07-16 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='is_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
