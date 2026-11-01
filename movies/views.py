import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .forms import MovieForm
from .models import Movie
from .utils import (
    DATA_DIR, generate_filename, save_movies_to_file,
    parse_file, validate_data, detect_format,
)

def index(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            data = {
                'title': form.cleaned_data['title'],
                'director': form.cleaned_data['director'],
                'year': form.cleaned_data['year'],
                'genre': form.cleaned_data['genre'],
                'rating': form.cleaned_data['rating'],
            }
            
            if form.cleaned_data['storage'] == 'db':
                if Movie.objects.filter(title=data['title'], director=data['director'], year=data['year']).exists():
                    messages.warning(request, 'Такой фильм уже есть в базе данных!')
                else:
                    Movie.objects.create(**data)
                    messages.success(request, 'Фильм успешно добавлен в БД.')
                    return redirect('movies:list_all')
            else:
                fmt = form.cleaned_data['format'] or 'json'
                filename = save_movies_to_file([data], fmt)
                messages.success(request, f'Фильм сохранён в файл {filename}')
                return redirect('movies:list_all')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = MovieForm()
    return render(request, 'movies/index.html', {'form': form})


def upload_file(request):
    if request.method == 'POST':
        uploaded = request.FILES.get('datafile')
        if not uploaded:
            messages.error(request, 'Файл не выбран.')
            return redirect('movies:upload')

        fmt = detect_format(uploaded.name)
        if fmt is None:
            messages.error(request, 'Разрешены только файлы .json и .xml.')
            return redirect('movies:upload')

        safe_name = generate_filename(fmt, original=uploaded.name)
        path = os.path.join(DATA_DIR, safe_name)

        with open(path, 'wb+') as dest:
            for chunk in uploaded.chunks():
                dest.write(chunk)

        try:
            data = parse_file(path, fmt)
            ok, err = validate_data(data)
        except Exception as exc:
            ok, err = False, f'ошибка разбора: {exc}'

        if not ok:
            if os.path.exists(path):
                os.remove(path)
            messages.error(request, f'Файл невалиден и удалён: {err}.')
        else:
            messages.success(request, f'Файл «{uploaded.name}» загружен как {safe_name}.')
        return redirect('movies:upload')

    return render(request, 'movies/upload.html')


def list_all(request):
    source = request.GET.get('source', 'db')
    movies_db = []
    files_data = []

    if source == 'db':
        movies_db = Movie.objects.all()
    else:
        if os.path.isdir(DATA_DIR):
            for name in sorted(os.listdir(DATA_DIR)):
                path = os.path.join(DATA_DIR, name)
                if not os.path.isfile(path): continue
                fmt = detect_format(name)
                if not fmt: continue

                entry = {'name': name, 'fmt': fmt, 'movies': [], 'error': None}
                try:
                    data = parse_file(path, fmt)
                    ok, err = validate_data(data)
                    if not ok: entry['error'] = err
                    else:
                        entry['movies'] = data if isinstance(data, list) else [data]
                except Exception as exc:
                    entry['error'] = str(exc)
                files_data.append(entry)

    return render(request, 'movies/list_all.html', {
        'source': source,
        'movies_db': movies_db,
        'files_data': files_data,
    })


def ajax_search(request):
    q = request.GET.get('q', '').strip()
    qs = Movie.objects.all()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(director__icontains=q) | 
            Q(genre__icontains=q)
        )
    
    results = []
    for m in qs:
        results.append({
            'id': m.id,
            'title': m.title,
            'director': m.director,
            'year': m.year,
            'genre': m.get_genre_display(),
            'rating': m.rating
        })
    return JsonResponse({'results': results})


def edit_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            dup = Movie.objects.exclude(pk=pk).filter(
                title=d['title'], director=d['director'], year=d['year']
            ).exists()
            if dup:
                messages.error(request, 'Такая запись уже существует в БД!')
            else:
                movie.title = d['title']
                movie.director = d['director']
                movie.year = d['year']
                movie.genre = d['genre']
                movie.rating = d['rating']
                movie.save()
                messages.success(request, 'Запись обновлена.')
                return redirect('movies:list_all')
    else:
        form = MovieForm(initial={
            'title': movie.title, 'director': movie.director,
            'year': movie.year, 'genre': movie.genre, 'rating': movie.rating,
        })
    return render(request, 'movies/edit.html', {'form': form, 'movie': movie})


def delete_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        movie.delete()
        messages.success(request, 'Запись удалена.')
        return redirect('movies:list_all')
    return render(request, 'movies/delete.html', {'movie': movie})