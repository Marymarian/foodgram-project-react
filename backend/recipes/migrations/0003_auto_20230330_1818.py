# Generated by Django 2.2.27 on 2023-03-30 15:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20230327_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientsinrecipe',
            name='amount',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1, 'В рецепте должны быть ингредиенты.')], verbose_name='Количество в рецепте'),
        ),
    ]