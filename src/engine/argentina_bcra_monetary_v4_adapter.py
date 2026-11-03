"""Official BCRA monetary statistics v4 API; preserves original metadata."""
import release_runtime
import json
import subprocess
from datetime import date
from urllib.parse import urlencode
BASE = 'https://api.bcra.gob.ar/estadisticas/v4.0/'

def _get(path, params):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    result = release_runtime.run(['/usr/bin/curl', '-q', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if result.returncode:
        raise RuntimeError('BCRA request failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    if len(result.stdout) > 8388608:
        raise RuntimeError('BCRA response exceeds 8 MiB')
    payload = json.loads(result.stdout)
    if payload.get('status') != 200:
        raise RuntimeError('BCRA returned error: ' + str(payload.get('errorMessages', payload.get('status'))))
    return payload

def _page(offset, limit):
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 3000):
        raise ValueError('offset >= 0; limit 1..3000')
    return {'offset': offset, 'limit': limit}

def _id(value):
    value = str(value)
    if not value.isascii() or not value.isdigit() or int(value) < 1:
        raise ValueError('variable ID must be a positive integer')
    return value

def catalog(offset=0, limit=100, categoria=None, tipo_serie=None, periodicidad=None, unidad=None):
    params = _page(offset, limit)
    for name, value in [('categoria', categoria), ('tipoSerie', tipo_serie), ('periodicidad', periodicidad), ('unidadExpresion', unidad)]:
        if value is not None:
            params[name] = value
    return _get('monetarias', params)

def observations(variable, start, end, offset=0, limit=100):
    start_date, end_date = (date.fromisoformat(start), date.fromisoformat(end))
    if start_date > end_date:
        raise ValueError('start must not exceed end')
    params = _page(offset, limit)
    params.update({'desde': start_date.isoformat(), 'hasta': end_date.isoformat()})
    return _get('monetarias/' + _id(variable), params)

def methodology(variable):
    return _get('metodologia/' + _id(variable), {})
