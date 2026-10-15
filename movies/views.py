import os
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import MovieForm
from .utils import (
    DATA_DIR, generate_filename, save_movies_to_file,
    parse_file, validate_data, detect_format,
)


def index(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        fmt = (request.POST.get('format') or 'json').lower()
        if fmt not in ('json', 'xml'):
            fmt = 'json'

        if form.is_valid():
            filename = save_movies_to_file([form.cleaned_data], fmt)
            messages.success(request, f'Фильм сохранён в файл {filename}')
            return redirect('movies:list_files')
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
            messages.error(request, f'Файл невалиден и был удалён: {err}.')
        else:
            messages.success(
                request,
                f'Файл «{uploaded.name}» успешно загружен как {safe_name}.'
            )
        return redirect('movies:upload')

    return render(request, 'movies/upload.html')


def list_files(request):
    files = []

    if os.path.isdir(DATA_DIR):
        for name in sorted(os.listdir(DATA_DIR)):
            path = os.path.join(DATA_DIR, name)
            if not os.path.isfile(path):
                continue
            fmt = detect_format(name)
            if fmt is None:
                continue

            entry = {'name': name, 'fmt': fmt, 'movies': [], 'error': None}
            try:
                data = parse_file(path, fmt)
                ok, err = validate_data(data)
                if not ok:
                    entry['error'] = err
                else:
                    if isinstance(data, dict):
                        data = [data]
                    entry['movies'] = data
            except Exception as exc:
                entry['error'] = str(exc)

            files.append(entry)

    return render(request, 'movies/list_files.html', {'files': files})