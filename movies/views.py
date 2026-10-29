from django.db import IntegrityError
from .models import Movie

def index(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            data = {k: form.cleaned_data[k]
                    for k in ('title', 'director', 'year', 'genre', 'rating')}

            if form.cleaned_data['storage'] == 'db':
                if Movie.objects.filter(**{k: data[k]
                        for k in ('title', 'director', 'year')}).exists():
                    messages.warning(request, 'Такой фильм уже есть в БД.')
                else:
                    Movie.objects.create(**data)
                    messages.success(request, 'Фильм добавлен в БД.')
                    return redirect('movies:list_all')
            else:
                fmt = form.cleaned_data['format'] or 'json'
                filename = save_movies_to_file([data], fmt)
                messages.success(request, f'Сохранено в файл {filename}')
                return redirect('movies:list_all')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = MovieForm()
    return render(request, 'movies/index.html', {'form': form})