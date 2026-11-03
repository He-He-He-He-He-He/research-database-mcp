"""Public UK police data API, monthly street-level approximations."""
import release_runtime
import datetime
import math
import re
import requests
BASE = 'https://data.police.uk/api/'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=45, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    return r.json()

def _month(value):
    if not isinstance(value, str) or not re.fullmatch('\\d{4}-\\d{2}', value):
        raise ValueError('date must have format YYYY-MM')
    try:
        datetime.date.fromisoformat(value + '-01')
    except ValueError:
        raise ValueError('invalid month') from None
    return value

def latest():
    return _get('crime-last-updated')

def categories(date):
    return _get('crime-categories', {'date': _month(date)})

def crimes(lat, lng, date, category='all-crime'):
    if isinstance(lat, bool) or isinstance(lng, bool) or (not all((isinstance(v, (int, float)) and math.isfinite(v) for v in (lat, lng)))) or (not (-90 <= lat <= 90 and -180 <= lng <= 180)):
        raise ValueError('invalid latitude or longitude')
    if not isinstance(category, str) or not re.fullmatch('[a-z0-9-]+', category):
        raise ValueError('invalid category')
    return _get('crimes-street/' + category, {'lat': lat, 'lng': lng, 'date': _month(date)})
