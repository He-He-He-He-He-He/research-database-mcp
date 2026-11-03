"""UN System Data Commons v2 public graph and cross-country observations.

Official UN guide: https://github.com/UNStats/OpenSourceWeek2026 . This is a
separate current UN Data Commons service from the legacy UNdata SDMX API.
Data are federated; source, date, unit and methods vary by observation facet.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://unsd-datacommons.gcp.un-icc.cloud/core/api/v2'
MAX_BYTES = 8000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('UN Data Commons request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response exceeds 8 MB')
    return {'source': url, 'response': json.loads(r.stdout)}

def metadata(variable):
    if not isinstance(variable, str) or not re.fullmatch('[A-Za-z0-9_./-]{1,200}', variable):
        raise ValueError('invalid variable identifier')
    return _get('/node', [('nodes', variable), ('property', '->[name,populationType]')])

def regional_latest(variable, region='africa'):
    if not isinstance(variable, str) or not re.fullmatch('[A-Za-z0-9_./-]{1,200}', variable):
        raise ValueError('invalid variable identifier')
    if region not in ('africa', 'asia', 'europe', 'oceania'):
        raise ValueError('unsupported region identifier')
    p = [('date', 'LATEST'), ('variable.dcids', variable), ('entity.expression', region + '<-containedInPlace+{typeOf:Country}')]
    p += [('select', v) for v in ('date', 'value', 'variable', 'entity', 'facet')]
    result = _get('/observation', p)
    if 'byVariable' not in result['response']:
        raise ValueError('unexpected observation response')
    result['note'] = 'LATEST selects the latest observation separately for each source facet, so one country can have multiple years and values. Inspect every facet for source, unit and periodicity; sources include non-official or collaborative providers and may repeat underlying data.'
    return result
