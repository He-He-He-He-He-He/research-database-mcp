"""World Bank Poverty and Inequality Platform public API.

Returns source fields unchanged, including PPP conversion factor, welfare type and survey years.
Headcount is a proportion, not a percentage. Survey income and consumption
measures may differ and are not always directly comparable. The default
poverty line and PPP vintage can change with upstream releases.
"""
import release_runtime
import math
import re
import requests
BASE = 'https://api.worldbank.org/pip/v1/'

def _get(path, params):
    response = requests.get(BASE + path, params=params, timeout=45)
    response.raise_for_status()
    return response.json()

def valid_params(endpoint='pip'):
    if endpoint not in ('pip', 'aux'):
        raise ValueError('endpoint must be pip or aux')
    return _get('valid-params', {'endpoint': endpoint})

def auxiliary(table='dictionary'):
    if not re.fullmatch('[a-z][a-z0-9_]{0,60}', table):
        raise ValueError('invalid auxiliary table name')
    return _get('aux', {'table': table, 'format': 'json'})

def statistics(country, year='all', poverty_line=None):
    """Retrieve one ISO-3 country's survey-based series at a chosen line.

    poverty_line is in international dollars per person per day; see returned
    release documentation for the PPP vintage; the returned `ppp` is a
    conversion factor, not the vintage. `all` uses survey years.
    """
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be a three-letter uppercase code')
    if not (year == 'all' or (isinstance(year, int) and (not isinstance(year, bool)) and (1900 <= year <= 2100))):
        raise ValueError('year must be all or a year from 1900 to 2100')
    params = {'country': country, 'year': year, 'format': 'json'}
    if poverty_line is not None:
        if isinstance(poverty_line, bool) or not isinstance(poverty_line, (int, float)) or (not math.isfinite(poverty_line)) or (poverty_line <= 0):
            raise ValueError('poverty_line must be a positive finite number')
        params['povline'] = poverty_line
    return _get('pip', params)
