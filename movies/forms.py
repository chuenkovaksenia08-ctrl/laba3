import datetime
from django import forms

GENRES = [
    ('action', 'Боевик'),
    ('comedy', 'Комедия'),
    ('drama', 'Драма'),
    ('thriller', 'Триллер'),
    ('fantasy', 'Фантастика'),
    ('horror', 'Ужасы'),
    ('animation', 'Анимация'),
    ('documentary', 'Документальный'),
]

CURRENT_YEAR = datetime.date.today().year #2026
FIRST_MOVIE_YEAR = 1888


class MovieForm(forms.Form):
    title = forms.CharField(label='Название', max_length=200, min_length=1)
    director = forms.CharField(label='Режиссёр', max_length=200, min_length=1)
    year = forms.IntegerField(
        label='Год выпуска',
        min_value=FIRST_MOVIE_YEAR,
        max_value=CURRENT_YEAR,
    )
    genre = forms.ChoiceField(label='Жанр', choices=GENRES)
    rating = forms.FloatField(label='Рейтинг (0–10)', min_value=0.0, max_value=10.0)

    def clean_title(self):
        value = self.cleaned_data['title'].strip()
        if not value:
            raise forms.ValidationError('Название не может быть пустым.')
        if value[:1].isdigit():
            raise forms.ValidationError('Название не может начинаться с цифры.')
        return value

    def clean_director(self):
        value = self.cleaned_data['director'].strip()
        if len(value) < 2:
            raise forms.ValidationError('Слишком короткое имя режиссёра.')
        return value
        STORAGE_CHOICES = [('db', 'База данных'), ('file', 'Файл')]
FORMAT_CHOICES  = [('json', 'JSON'), ('xml', 'XML')]

class MovieForm(forms.Form):
    # ... существующие поля title/director/year/genre/rating ...

    storage = forms.ChoiceField(
        label='Куда сохранить', choices=STORAGE_CHOICES,
        initial='db', widget=forms.RadioSelect,
    )
    format = forms.ChoiceField(
        label='Формат файла', choices=FORMAT_CHOICES,
        required=False, initial='json',
    )