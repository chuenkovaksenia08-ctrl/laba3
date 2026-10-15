import os
import re
import json
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom

from django.conf import settings

DATA_DIR = os.path.join(settings.MEDIA_ROOT, 'movies_data')
os.makedirs(DATA_DIR, exist_ok=True)

MOVIE_FIELDS = ['title', 'director', 'year', 'genre', 'rating']
ALLOWED_EXT = {'json', 'xml'}


def sanitize_filename(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r'[^A-Za-z0-9._-]', '_', base)
    base = base.strip('._') or 'file'
    return base[:100]


def generate_filename(ext: str, original: str | None = None) -> str:
    prefix = 'upload' if original else 'movies'
    return f"{prefix}_{uuid.uuid4().hex}.{ext}"


def validate_movie_dict(movie) -> tuple[bool, str]:
    if not isinstance(movie, dict):
        return False, 'элемент не является объектом'
    for field in MOVIE_FIELDS:
        if field not in movie:
            return False, f'отсутствует поле «{field}»'
    try:
        year = int(movie['year'])
    except (TypeError, ValueError):
        return False, 'поле «year» должно быть целым числом'
    if not (1888 <= year <= 2100):
        return False, 'год вне допустимого диапазона'
    try:
        rating = float(movie['rating'])
    except (TypeError, ValueError):
        return False, 'поле «rating» должно быть числом'
    if not (0.0 <= rating <= 10.0):
        return False, 'рейтинг должен быть в диапазоне 0–10'
    if not str(movie['title']).strip():
        return False, 'пустое название фильма'
    if not str(movie['director']).strip():
        return False, 'пустой режиссёр'
    return True, ''


def validate_data(data) -> tuple[bool, str]:
    if isinstance(data, list):
        if not data:
            return False, 'файл не содержит ни одного фильма'
        for i, item in enumerate(data):
            ok, err = validate_movie_dict(item)
            if not ok:
                return False, f'элемент {i}: {err}'
        return True, ''
    if isinstance(data, dict):
        return validate_movie_dict(data)
    return False, 'неверная структура данных'


def _movie_to_clean_dict(movie: dict) -> dict:
    return {
        'title':    str(movie['title']).strip(),
        'director': str(movie['director']).strip(),
        'year':     int(movie['year']),
        'genre':    str(movie['genre']),
        'rating':   float(movie['rating']),
    }


def save_movies_to_file(movies: list[dict], fmt: str) -> str:
    fmt = fmt.lower()
    if fmt not in ALLOWED_EXT:
        raise ValueError('Недопустимый формат')
    movies = [_movie_to_clean_dict(m) for m in movies]
    filename = generate_filename(fmt)
    path = os.path.join(DATA_DIR, filename)

    if fmt == 'json':
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
    else:
        root = ET.Element('movies')
        for m in movies:
            node = ET.SubElement(root, 'movie')
            for key in MOVIE_FIELDS:
                el = ET.SubElement(node, key)
                el.text = str(m[key])
        raw = ET.tostring(root, encoding='utf-8')
        pretty = minidom.parseString(raw).toprettyxml(indent='  ', encoding='utf-8')
        with open(path, 'wb') as f:
            f.write(pretty)
    return filename


def parse_file(path: str, fmt: str):
    fmt = fmt.lower()
    if fmt == 'json':
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    if fmt == 'xml':
        tree = ET.parse(path)
        root = tree.getroot()
        if root.tag != 'movies':
            raise ValueError('корневой элемент должен называться <movies>')
        movies = []
        for node in root.findall('movie'):
            item = {}
            for field in MOVIE_FIELDS:
                el = node.find(field)
                item[field] = el.text if el is not None else None
            movies.append(item)
        return movies
    raise ValueError('Неподдерживаемый формат')


def detect_format(filename: str) -> str | None:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext if ext in ALLOWED_EXT else None