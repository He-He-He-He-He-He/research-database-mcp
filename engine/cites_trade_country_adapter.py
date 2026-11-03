"""Bounded CITES official annual trade comparative table by reporting trade country."""
import release_runtime
import csv
import io
import re
import requests
BASE = 'https://trade.cites.org'

def countries():
    r = requests.get(BASE + '/api/v1/geo_entities', params={'geo_entity_types_set': 4, 'locale': 'en'}, timeout=30)
    r.raise_for_status()
    return r.json()['geo_entities']

def query(country_code, year, *, role='exporter', limit=50, offset=0):
    if not re.fullmatch('[A-Z]{2}', country_code) or type(year) is not int or (not 1975 <= year <= 2026):
        raise ValueError('country code must be ISO2 and year 1975..2026')
    if role not in ('importer', 'exporter') or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid role or limit')
    matches = [x for x in countries() if x.get('iso_code2') == country_code]
    if len(matches) != 1:
        raise ValueError('country code missing or ambiguous in official directory')
    ident = str(matches[0]['id'])
    p = {'filters[time_range_start]': str(year), 'filters[time_range_end]': str(year), 'filters[exporters_ids][]': ident if role == 'exporter' else 'all_exp', 'filters[importers_ids][]': ident if role == 'importer' else 'all_imp', 'filters[sources_ids][]': 'all_sou', 'filters[purposes_ids][]': 'all_pur', 'filters[terms_ids][]': 'all_ter', 'filters[selection_taxon]': 'taxonomic_cascade', 'filters[taxon_concepts_ids][]': ''}
    with requests.Session() as s:
        response = s.get(BASE + '/en/cites_trade/exports/download.json', params=p, timeout=60)
        response.raise_for_status()
        count = response.json()['total']
        if count > 10000:
            raise ValueError('source query exceeds 10000 raw records; use narrower website filters')
        if count == 0:
            return {'source': 'CITES Trade Database', 'country': matches[0], 'year': year, 'role': role, 'raw_count': 0, 'comparative_rows': 0, 'offset': offset, 'returned': 0, 'next_offset': None, 'truncated': False, 'records': []}
        p.update({'filters[report_type]': 'comptab', 'filters[csv_separator]': 'comma'})
        with s.get(BASE + '/en/cites_trade/exports/download', params=p, timeout=60, stream=True) as r:
            r.raise_for_status()
            body = r.raw.read(5000001, decode_content=True)
            if 'csv' not in r.headers.get('content-type', '').lower():
                raise ValueError('source did not return CSV')
            source_url = r.url
        if len(body) > 5000000:
            raise ValueError('CSV exceeds size limit')
    rows = list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
    if rows and (not {'Importer reported quantity', 'Exporter reported quantity', 'Unit', 'Taxon'}.issubset(rows[0])):
        raise ValueError('unexpected CITES table')
    return {'source': 'CITES Trade Database, UNEP-WCMC for CITES Secretariat', 'source_url': source_url, 'country': matches[0], 'year': year, 'role': role, 'raw_count': count, 'comparative_rows': len(rows), 'offset': offset, 'returned': len(rows[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(rows) else None, 'truncated': offset + limit < len(rows), 'records': rows[offset:offset + limit], 'note': 'Importer- and exporter-reported quantities are separate reports and must not be added. Records are reported CITES trade, not proof of actual shipment or illegal trade; units, purpose and source differ. Cite the source and consult its use guidance; redistribution rights are not verified. Comparative rows and raw reports have different counts. Each request refetches the report; ordering may change between requests.'}
