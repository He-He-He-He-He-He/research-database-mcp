"""World Bank CCKP public raster catalogue and parameterised climate API.

Catalogue files are gridded rasters; their existence does not guarantee that
identical combinations are supported by the separate national aggregation API.
"""
import release_runtime
import argparse
import json
import re
import xml.etree.ElementTree as ET
import requests
CATALOG = 'https://wbg-cckp.s3.amazonaws.com/'
API = 'https://cckpapi.worldbank.org/cckp/v1/'
DOC = 'https://worldbank.github.io/climateknowledgeportal/README.html'
API_DOC = 'https://climateknowledgeportal.worldbank.org/download-data'
NS = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}

def catalogue(prefix='data/', limit=100, continuation=None):
    if not re.fullmatch('data/(?:[A-Za-z0-9_.-]+/)*', prefix) or '..' in prefix:
        raise ValueError('prefix must be a directory under data/, e.g. data/cmip6-x0.25/tas/')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be 1..1000')
    params = {'list-type': '2', 'prefix': prefix, 'delimiter': '/', 'max-keys': limit}
    if continuation:
        if len(continuation) > 4096:
            raise ValueError('continuation token too long')
        params['continuation-token'] = continuation
    r = requests.get(CATALOG, params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    directories = [x.text for x in root.findall('s:CommonPrefixes/s:Prefix', NS)]
    files = [{'key': x.findtext('s:Key', namespaces=NS), 'size_bytes': x.findtext('s:Size', namespaces=NS), 'last_modified': x.findtext('s:LastModified', namespaces=NS), 'etag': x.findtext('s:ETag', namespaces=NS)} for x in root.findall('s:Contents', NS) if x.findtext('s:Key', namespaces=NS) != prefix]
    truncated = root.findtext('s:IsTruncated', namespaces=NS) == 'true'
    return {'provider': 'World Bank CCKP', 'source': CATALOG, 'documentation': DOC, 'prefix': prefix, 'directories': directories, 'files': files, 'truncated': truncated, 'next_continuation_token': root.findtext('s:NextContinuationToken', namespaces=NS), 'note': 'Public S3 gridded raster file catalogue, not the separate country API inventory. File modification time is not necessarily initial publication time. Individual file metadata, units, licenses and spatial resolution should be checked before use.'}

def query(collection, datatype, variables, product, aggregation, period, percentile, scenario, model, model_calculation, statistic, geography):
    fields = [collection, datatype, variables, product, aggregation, period, percentile, scenario, model, model_calculation, statistic]
    for value in fields:
        if not isinstance(value, str) or len(value) > 250 or (not re.fullmatch('[A-Za-z0-9.,-]+', value)):
            raise ValueError('CCKP parameter fields may contain only letters, digits, comma, dot and hyphen')
    if not isinstance(geography, str) or not re.fullmatch('[A-Za-z0-9.-]{1,80}', geography):
        raise ValueError('invalid geography code')
    path = '_'.join(fields) + '/' + geography
    r = requests.get(API + path, params={'_format': 'json'}, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('metadata'), dict) or (not isinstance(j.get('data'), (dict, list))):
        raise ValueError('unexpected CCKP response')
    if j['metadata'].get('status') != 'success':
        raise RuntimeError('CCKP returned a non-success status: ' + str(j['metadata'].get('messages'))[:500])
    return {'provider': 'World Bank Climate Change Knowledge Portal', 'source': r.url, 'documentation': API_DOC, 'selection': dict(zip(['collection', 'data_type', 'variables', 'product', 'aggregation', 'period', 'percentile', 'scenario', 'model', 'model_calculation', 'statistic', 'geography'], fields + [geography])), 'response': j, 'note': 'Raw upstream data and time keys retained; national values represent spatial aggregation, not a single weather station. Historical and projected/modelled datasets differ. Future SSP scenarios are model projections, not observations or predictions of certainty. Consult variable metadata for units, aggregation, uncertainty and interpretation. Current API response is not evidence of a historical data vintage.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('catalogue')
    c.add_argument('--prefix', default='data/')
    c.add_argument('--limit', type=int, default=100)
    c.add_argument('--continuation')
    q = sub.add_parser('query')
    for name in ['collection', 'datatype', 'variables', 'product', 'aggregation', 'period', 'percentile', 'scenario', 'model', 'model_calculation', 'statistic', 'geography']:
        q.add_argument(name)
    a = vars(p.parse_args())
    cmd = a.pop('command')
    print(json.dumps(catalogue(**a) if cmd == 'catalogue' else query(**a), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
