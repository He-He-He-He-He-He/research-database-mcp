"""Norwegian Offshore Directorate historical field production profiles."""
import release_runtime
import re
import requests
URL = 'https://factmaps.sodir.no/api/rest/services/DataService/Data/FeatureServer/7300'
NOTES = ['Norwegian Offshore Directorate: historical offshore production profiles from DISKOS; this layer does not provide forecasts.', 'Month and year records overlap: never sum both together. prfMonth 0 belongs to annual rows, not a zero month.', 'Oil and NGL fields are in million standard cubic metres, gas in billion standard cubic metres, and investments in million nominal NOK; consult field aliases and original documentation.', 'Net, gross, condensate, oil-equivalent and produced water are different measures. Zero and null remain distinct. Data may be revised; observation date does not establish an earlier publication vintage.', 'Source data are made available under Norwegian Licence for Open Government Data; attribution and other conditions apply.']

def _get(path='', params=None):
    r = requests.get(URL + path, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('SODIR service error: ' + str(j.get('error', 'invalid response')))
    return j

def metadata():
    j = _get(params={'f': 'json'})
    if not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected metadata')
    return {'source': URL, 'notes': NOTES, 'metadata': j}

def records(field, year, period='month', limit=20, offset=0):
    if not isinstance(field, str) or not re.fullmatch('[A-Z0-9 -]{1,70}', field):
        raise ValueError('Field must contain uppercase letters, digits, spaces or hyphens')
    if type(year) is not int or not 1960 <= year <= 2100 or period not in ('month', 'year') or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('Invalid year, period or pagination')
    where = "prfInformationCarrier = '%s' AND prfYear = %d AND prfPeriod = '%s'" % (field, year, period)
    j = _get('/query', {'f': 'json', 'where': where, 'outFields': '*', 'returnGeometry': 'false', 'orderByFields': 'prfMonth ASC, OBJECTID ASC', 'resultOffset': offset, 'resultRecordCount': limit})
    if not isinstance(j.get('features'), list):
        raise ValueError('Unexpected response')
    return {'source': URL + '/query', 'field': field, 'year': year, 'period': period, 'offset': offset, 'notes': NOTES, 'response': j}
