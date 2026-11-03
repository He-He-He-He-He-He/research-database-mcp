"""UN Statistics Division Monthly Bulletin of Statistics official SOAP service."""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
URL = 'https://unstats.un.org/unsd/mbs/api/wsMbsServices.asmx'
DOC = URL + '?op=GetDataSeriesXML'
NS = 'http://unstats.un.org/unsd/mbs'
SOAP = 'http://schemas.xmlsoap.org/soap/envelope/'

def _call(op, args):
    env = ET.Element('{%s}Envelope' % SOAP)
    body = ET.SubElement(env, '{%s}Body' % SOAP)
    node = ET.SubElement(body, '{%s}%s' % (NS, op))
    for key, value in args.items():
        ET.SubElement(node, '{%s}%s' % (NS, key)).text = str(value)
    xml = ET.tostring(env, encoding='utf-8', xml_declaration=True)
    with requests.post(URL, data=xml, headers={'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': '"%s/%s"' % (NS, op)}, timeout=(15, 35), stream=True) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 5000000:
                raise RuntimeError('UN MBS response exceeds 5 MB; narrow request')
            parts.append(chunk)
    root = ET.fromstring(b''.join(parts))
    fault = root.find('.//{%s}Fault' % SOAP)
    if fault is not None:
        raise RuntimeError('UN MBS SOAP fault: ' + ''.join(fault.itertext())[:300])
    result = root.find('.//{%s}%sResult' % (NS, op))
    if result is None or len(result) != 1:
        raise RuntimeError('Unexpected UN MBS XML response')
    return result[0]

def _row(element):
    return {x.tag.split('}')[-1]: x.text for x in element}

def catalogue(kind, keyword='', offset=0, limit=50):
    types = {'series': ('GetMetadataSeriesXML', 'MbsSerie'), 'countries': ('GetMetadataCountriesXML', 'MbsCountry'), 'periods': ('GetMetadataDateCodeXML', 'MbsDateCode')}
    if kind not in types or not isinstance(keyword, str) or len(keyword) > 100 or (not isinstance(offset, int)) or isinstance(offset, bool) or (offset < 0) or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid catalogue kind or filter')
    op, item = types[kind]
    root = _call(op, {})
    rows = [_row(x) for x in root.iter() if x.tag.split('}')[-1] == item]
    if not rows:
        raise RuntimeError('Unexpected empty MBS catalogue or schema')
    term = keyword.casefold()
    matched = [r for r in rows if term in str(r).casefold()]
    return {'source': 'UN Statistics Division Monthly Bulletin of Statistics', 'documentation': DOC, 'kind': kind, 'total': len(rows), 'matched': len(matched), 'offset': offset, 'items': matched[offset:offset + limit]}

def data(series, country, start, end, period='Y'):
    if not isinstance(series, str) or not re.fullmatch('[A-Za-z0-9]{4}', series):
        raise ValueError('Series must be four alphanumeric characters')
    if not isinstance(country, str) or not re.fullmatch('\\d{1,3}', country) or int(country) == 0:
        raise ValueError('Specify one nonzero UN M49 country code')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}', start)) or (not re.fullmatch('\\d{4}', end)) or (start > end) or (int(end) - int(start) > 30) or (period not in ('M', 'Q', 'Y', 'A')):
        raise ValueError('Invalid year range or period')
    root = _call('GetDataSeriesXML', {'sid': series, 'cid': country, 'yearfrom': start, 'yearto': end, 'p': period})
    if root.tag.split('}')[-1] != 'MbsSeriesSet':
        raise RuntimeError('Unexpected MBS data schema')
    package = root.find('MbsPackageInfo')
    rows = [_row(x) for x in root.findall('MbsDataSeries')]
    notes = [_row(x) for x in root.findall('MbsFootnotes')]
    if package is None:
        raise RuntimeError('Missing MBS package metadata')
    meta = _row(package)
    if not str(meta.get('TotalDataPoints', '')).isdigit() or int(meta['TotalDataPoints']) != len(rows) or (not str(meta.get('TotalFootnotes', '')).isdigit()) or (int(meta['TotalFootnotes']) != len(notes)):
        raise RuntimeError('MBS response counts do not match the returned records')
    if meta.get('RequestedSeries', '').upper() != series.upper() or int(meta.get('RequestedCountryList', '-1')) != int(country):
        raise RuntimeError('MBS returned unexpected request metadata')
    if any((r.get('SeriesCode', '').upper() != series.upper() or int(r.get('CountryCode', '-1')) != int(country) for r in rows)):
        raise RuntimeError('MBS returned unexpected series or country')
    return {'source': 'United Nations Statistics Division Monthly Bulletin of Statistics', 'documentation': DOC, 'package': meta, 'items': rows, 'footnotes': notes, 'note': 'Original values, unit/base, dimensions, time codes and notes are retained as strings; check footnotes and definitions. Empty results do not imply zero.'}
