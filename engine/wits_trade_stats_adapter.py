"""World Bank WITS Trade Stats public metadata and SDMX JSON data.

Documentation: https://wits.worldbank.org/witsapiintro.aspx
Raw SDMX JSON includes dimensions, units and observation attributes; decode them
using the accompanying structure. Trade values and development indicators have
separate source databases, so do not assume one source or unit across indicators.
"""
import release_runtime
import json
import re
import subprocess
import xml.etree.ElementTree as ET
BASE = 'https://wits.worldbank.org/API/V1'
MAX_BYTES = 8000000
SOURCES = ('tradestats-trade', 'tradestats-tariff', 'tradestats-development')

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--location', '--proto-redir', '=https', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('WITS request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('WITS response too large')
    return r.stdout.decode('utf-8-sig')

def _source(value):
    if value not in SOURCES:
        raise ValueError('unsupported trade statistics source')
    return value

def _code(value, name):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', value):
        raise ValueError('invalid ' + name)
    if value.lower() == 'all':
        raise ValueError('use a specific ' + name + ' to limit results')
    return value

def indicators(source, keyword=''):
    source = _source(source)
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    path = '/wits/datasource/' + source + '/indicator/all'
    root = ET.fromstring(_get(path))
    result = []
    for node in root.iter():
        if node.tag.split('}')[-1] != 'indicator':
            continue
        entry = {'attributes': dict(node.attrib), 'fields': {x.tag.split('}')[-1]: ''.join(x.itertext()) for x in node}}
        if keyword.casefold() in json.dumps(entry, ensure_ascii=False).casefold():
            result.append(entry)
    return {'source': BASE + path, 'matched': len(result), 'indicators': result}

def data(source, reporter, year, indicator, partner=None, product=None):
    source = _source(source)
    reporter = _code(reporter, 'reporter')
    indicator = _code(indicator, 'indicator')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1988 <= year <= 2100):
        raise ValueError('invalid year')
    if (partner is None) != (product is None):
        raise ValueError('provide both partner and product, or neither')
    if source == 'tradestats-tariff' and partner is None:
        raise ValueError('tariff requires partner and product')
    path = '/SDMX/V21/datasource/' + source + '/reporter/' + reporter + '/year/' + str(year)
    if partner is not None:
        path += '/partner/' + _code(partner, 'partner') + '/product/' + _code(product, 'product')
    path += '/indicator/' + indicator + '?format=JSON'
    obj = json.loads(_get(path))
    if not isinstance(obj, dict) or 'structure' not in obj or 'dataSets' not in obj:
        raise ValueError('unexpected WITS SDMX data response')
    return {'source': BASE + path, 'sdmx': obj, 'note': 'Series and observation numeric indexes refer to SDMX structure dimensions and attributes; preserve labels and units.'}
