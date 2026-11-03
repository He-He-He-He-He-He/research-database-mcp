"""Lao Statistics Bureau e-GDDS: official CPI, GDP and population SDMX XML."""
import release_runtime
import re, subprocess, xml.etree.ElementTree as ET
PAGE = 'https://www.lsb.gov.la/lsb-en.htm'
DATASETS = {'gdp': 'https://www.lsb.gov.la/E-GDDS/LSB/SDMX/GDP/GDP_Lao_PDR_SDMX.xml', 'cpi': 'https://www.lsb.gov.la/E-GDDS/LSB/SDMX/CPI/CPI_LaoPDR(TRN)_SDMX.xml', 'population': 'https://www.lsb.gov.la/E-GDDS/LSB/SDMX/POP/POP_Lao%20PDR_SDMX.xml'}

def _read(dataset):
    if dataset not in DATASETS:
        raise ValueError('dataset must be gdp, cpi or population')
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '35', '--max-filesize', '5000000', DATASETS[dataset]], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('Lao LSB download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 5000000 or b'<!DOCTYPE' in p.stdout.upper():
        raise RuntimeError('Unexpected or oversized XML')
    try:
        root = ET.fromstring(p.stdout)
    except ET.ParseError as e:
        raise RuntimeError('Invalid SDMX XML') from e
    if root.tag.rsplit('}', 1)[-1] != 'StructureSpecificData':
        raise RuntimeError('Unexpected SDMX schema')
    return [x for x in root.iter() if x.tag.rsplit('}', 1)[-1] == 'Series']

def catalogue(dataset, keyword='', offset=0, limit=25):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    series = _read(dataset)
    m = []
    for s in series:
        if keyword.casefold() not in ' '.join(s.attrib.values()).casefold():
            continue
        m.append({'attributes': s.attrib, 'observations': sum((c.tag.rsplit('}', 1)[-1] == 'Obs' for c in s))})
    return {'source': 'Lao Statistics Bureau e-GDDS', 'source_page': PAGE, 'dataset': dataset, 'dataset_url': DATASETS[dataset], 'matches': len(m), 'offset': offset, 'items': m[offset:offset + limit], 'note': 'Series codes and dimensional attributes are as published; consult original workbook and metadata for indicator definitions, coverage, units and multiplier before interpretation.'}

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
    data = []
    for s in _read(dataset):
        if s.attrib.get('INDICATOR') != indicator:
            continue
        obs = [dict(c.attrib) for c in s if c.tag.rsplit('}', 1)[-1] == 'Obs' and (not start or c.attrib.get('TIME_PERIOD', '') >= start) and (not end_bound or c.attrib.get('TIME_PERIOD', '') <= end_bound)]
        selected = obs[-limit:] if latest else obs[offset:offset + limit]
        data.append({'attributes': s.attrib, 'matched_observations': len(obs), 'items': selected})
    return {'source': 'Lao Statistics Bureau e-GDDS', 'source_page': PAGE, 'dataset': dataset, 'dataset_url': DATASETS[dataset], 'indicator': indicator, 'series_count': len(data), 'series': data, 'note': 'Original values, periods and attributes retained as strings; no multiplier applied, no rounding, currency conversion or imputation. latest means last rows in source order, not a guarantee of sort. CPI PCPI_IX is an index (base Dec 2015), not inflation; GDP/population multipliers and definitions require source verification. Population figures predate the 2025 census and may use a different methodology.'}
