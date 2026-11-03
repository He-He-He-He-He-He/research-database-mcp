"""Spain INE Tempus3 public statistics catalogue and time series.

Responses preserve labels, unit and scale codes, time period and secrecy flags;
series may be revised, discontinued, or based on different reference periods.
"""
import release_runtime
import re
import requests
BASE = 'https://servicios.ine.es/wstempus/js/'

def _get(path, params=None, language='EN'):
    if language not in ('EN', 'ES'):
        raise ValueError('language must be EN or ES')
    r = requests.get(BASE + language + '/' + path, params=params, timeout=40)
    r.raise_for_status()
    return r.json()

def _code(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_]{1,60}', value):
        raise ValueError('invalid identifier')
    return value

def operations(query='', language='EN'):
    data = _get('OPERACIONES_DISPONIBLES', language=language)
    return [x for x in data if query.casefold() in str(x).casefold()]

def tables(operation, language='EN'):
    return _get('TABLAS_OPERACION/' + _code(operation), language=language)

def table_series(table, language='EN'):
    if isinstance(table, bool) or not str(table).isdigit():
        raise ValueError('table must be numeric')
    return _get('SERIES_TABLA/' + str(table), language=language)

def series_metadata(series, language='EN'):
    return _get('SERIE/' + _code(series), language=language)

def observations(series, last=10, language='EN'):
    if isinstance(last, bool) or not isinstance(last, int) or (not 1 <= last <= 1000):
        raise ValueError('last must be 1..1000')
    return _get('DATOS_SERIE/' + _code(series), {'nult': last}, language)
