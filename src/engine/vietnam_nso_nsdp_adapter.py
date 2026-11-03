"""Vietnam National Statistics Office e-GDDS CPI, GDP, trade, population SDMX."""
import release_runtime
import re, subprocess, xml.etree.ElementTree as ET
PAGE = 'https://nsdp.nso.gov.vn/'
ROOT = 'https://nsdp.nso.gov.vn/GSO-chung/SDMXFiles/GSO/'
FILES = {'gdp': 'GDPVNM.xml', 'cpi': 'CPIVNM.xml', 'trade': 'METVNM.xml', 'population': 'POPVNM.xml'}

def _read(dataset):
    if dataset not in FILES:
        raise ValueError('dataset must be gdp, cpi, trade, or population')
    u = ROOT + FILES[dataset]
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '35', '--max-filesize', '5000000', u], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('Vietnam NSO download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 5000000 or b'<!DOCTYPE' in p.stdout.upper():
        raise RuntimeError('Unexpected or oversized XML')
    try:
        root = ET.fromstring(p.stdout)
    except ET.ParseError as e:
        raise RuntimeError('Invalid SDMX XML') from e
    if root.tag.rsplit('}', 1)[-1] != 'StructureSpecificData':
        raise RuntimeError('Unexpected SDMX schema')
    datasets = [x for x in root.iter() if x.tag.rsplit('}', 1)[-1] == 'DataSet']
    if len(datasets) != 1:
        raise RuntimeError('Unexpected dataset count')
    return (datasets[0].attrib, [x for x in datasets[0].iter() if x.tag.rsplit('}', 1)[-1] == 'Series'])

def catalogue(dataset, keyword='', offset=0, limit=25):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    attrs, series = _read(dataset)
    items = []
    for s in series:
        if keyword.casefold() not in ' '.join(s.attrib.values()).casefold():
            continue
        items.append({'attributes': s.attrib, 'observations': sum((c.tag.rsplit('}', 1)[-1] == 'Obs' for c in s))})
    return {'source': 'Vietnam National Statistics Office e-GDDS', 'source_page': PAGE, 'dataset_url': ROOT + FILES[dataset], 'dataset_attributes': attrs, 'matches': len(items), 'offset': offset, 'items': items[offset:offset + limit], 'note': 'Codes and dimension attributes are retained as published. The official trade dataset labels figures from January 2018 preliminary; verify scope, coverage, and units in the workbook and metadata.'}

def series(dataset, indicator, start='', end='', offset=0, limit=25, latest=False):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', indicator):
        raise ValueError('invalid indicator')
    if any((not isinstance(x, str) or (x and (not re.fullmatch('\\d{4}(?:-\\d{2})?', x))) for x in (start, end))):
        raise ValueError('periods must be YYYY or YYYY-MM')
    if any((len(x) == 7 and (not 1 <= int(x[-2:]) <= 12) for x in (start, end) if x)):
        raise ValueError('invalid month')
    end_bound = end + '-99' if len(end) == 4 else end
    if start and end and (start > end_bound):
        raise ValueError('start exceeds end')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100) or (not isinstance(latest, bool)):
        raise ValueError('invalid pagination')
    attrs, items = _read(dataset)
    data = []
    for s in items:
        if s.attrib.get('INDICATOR') != indicator:
            continue
        obs = [dict(c.attrib) for c in s if c.tag.rsplit('}', 1)[-1] == 'Obs' and (not start or c.attrib.get('TIME_PERIOD', '') >= start) and (not end_bound or c.attrib.get('TIME_PERIOD', '') <= end_bound)]
        data.append({'attributes': s.attrib, 'matched_observations': len(obs), 'items': obs[-limit:] if latest else obs[offset:offset + limit]})
    return {'source': 'Vietnam National Statistics Office e-GDDS', 'source_page': PAGE, 'dataset_url': ROOT + FILES[dataset], 'dataset_attributes': attrs, 'indicator': indicator, 'series_count': len(data), 'series': data, 'note': 'Values and UNIT_MULT remain as published; no currency conversion, rounding or multiplier applied. Trade dataset marks figures from Jan 2018 preliminary; exports FOB and imports CIF are not directly comparable valuation bases. CPI is an index, not inflation. Series update dates vary; latest uses source order, not guaranteed chronological sorting.'}
