import os
from csv import reader
from pathlib import PurePath
from recipes.models import Ingredients
from foodgram import settings

PROJECT_DIR = settings.BASE_DIR


def cvs_to_dj_model():
    """Функция конвертора данных cvs в БД средствами Django"""
    data_dir = os.fspath(PurePath(settings.BASE_DIR.resolve().parent, 'data'))
    file = f'{data_dir}/ingredients.csv'
    with open(file, newline='', encoding='utf-8') as f:
        for row in reader(f):
            if len(row) == 2:
                Ingredients.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )