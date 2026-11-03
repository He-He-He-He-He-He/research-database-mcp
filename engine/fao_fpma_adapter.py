"""FAO Food Price Monitoring and Analysis public time-series API.

Official API docs: https://fpma-documentation.web.app/docs/api-docs/intro/
Series metadata define original currency, market, product and measure unit.
Retail and wholesale prices, conversion and adjusted values must not be conflated.
"""
import release_runtime
import json, re, subprocess, uuid
from urllib.parse import urlencode
BASE = 'https://fpma.fao.org/giews/v4/global/price_module/api/v1'
MAX_BYTES = 10000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('FAO FPMA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('FPMA response exceeds 10 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or not isinstance(obj.get('results'), list):
        raise ValueError('unexpected FPMA response')
    return {'source': url, 'response': obj}

def series(country, page=1):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3 uppercase')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page must be positive')
    if page != 1:
        raise ValueError('FPMA country-series pagination is not verified; only page 1 is supported')
    result = _get('/FpmaSerie/', {'iso3_country_codes': country, 'page': page})
    if any((x.get('iso3_country_code') != country for x in result['response']['results'])):
        raise ValueError('FPMA returned a different country')
    result['note'] = '仅支持经验证的第 1 页；请结合上游 count 和 next 判断是否完整。不同市场、零售/批发、币种和计量单位不能直接混同。'
    return result

def prices(series_uuid, period='monthly'):
    if not isinstance(series_uuid, str):
        raise ValueError('invalid series UUID')
    try:
        canonical = str(uuid.UUID(series_uuid))
    except (ValueError, AttributeError):
        raise ValueError('invalid series UUID') from None
    if period not in ('daily', 'weekly', 'monthly'):
        raise ValueError('period must be daily, weekly or monthly')
    result = _get('/FpmaSeriePrice/', {'uuid__in': canonical, 'periodicity': period})
    if any((x.get('uuid') != canonical for x in result['response']['results'])):
        raise ValueError('FPMA returned a different series')
    result['note'] = 'Original price is in the series currency per measure unit; real and USD prices are separate fields. Obtain metadata from series() before interpretation.'
    return result
