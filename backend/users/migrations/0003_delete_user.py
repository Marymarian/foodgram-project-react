# Generated by Django 2.2.27 on 2023-03-27 12:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_role'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]