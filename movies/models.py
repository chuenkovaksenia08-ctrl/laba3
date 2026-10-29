from django.db import models

class Movie(models.Model):
    GENRES = [
        ('action', 'Боевик'), ('comedy', 'Комедия'),
        ('drama', 'Драма'), ('thriller', 'Триллер'),
        ('fantasy', 'Фантастика'), ('horror', 'Ужасы'),
        ('animation', 'Анимация'), ('documentary', 'Документальный'),
    ]

    title = models.CharField('Название', max_length=200)
    director = models.CharField('Режиссёр', max_length=200)
    year = models.IntegerField('Год выпуска')
    genre = models.CharField('Жанр', max_length=50, choices=GENRES)
    rating = models.FloatField('Рейтинг')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Защита от дубликатов на уровне БД
        unique_together = ('title', 'director', 'year')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.year})'