"""Maddison Project Database 2023 historical GDP per capita and population."""
import release_runtime
import io
import re
import openpyxl
import requests
URL = 'https://dataverse.nl/api/access/datafile/421302'

def query(country_code, indicator, year_from, year_to, *, local_file=None, limit=100):
    if not re.fullmatch('[A-Z]{3}', country_code) or indicator not in ('gdppc', 'population'):
        raise ValueError('invalid ISO3 or indicator')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not 1 <= year_from <= year_to <= 2022 or (not 1 <= limit <= 1000):
        raise ValueError('invalid years or limit')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=90) as r:
            r.raise_for_status()
            body = r.raw.read(10000001, decode_content=True)
        if len(body) > 10000000:
            raise ValueError('workbook exceeds size limit')
        w = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=True)
    try:
        s = w['GDPpc' if indicator == 'gdppc' else 'Population']
        rows = iter(s.values)
        names = next(rows)
        next(rows)
        codes = next(rows)
        if codes.count(country_code) != 1:
            raise ValueError('country not found or ambiguous')
        index = codes.index(country_code)
        out = []
        for row in rows:
            if type(row[0]) is int and year_from <= row[0] <= year_to:
                out.append({'year': row[0], 'value': row[index]})
        references = {}
        for title in ('Sources', 'Maddison original sources'):
            active = False
            found = []
            for row in w[title].values:
                marker = row[0]
                if isinstance(marker, str) and re.fullmatch('[A-Z]{3}', marker):
                    active = marker == country_code
                if active and row[2]:
                    found.append({'period': row[1], 'source': row[2]})
            references[title] = found
        return {'source': 'Local workbook (provenance and version unverified)' if local_file else 'Maddison Project Database 2023', 'source_url': local_file if local_file else URL, 'license': None if local_file else 'CC BY 4.0', 'country': names[index], 'country_code': country_code, 'indicator': indicator, 'unit': None if local_file else '2011 international dollars per person' if indicator == 'gdppc' else 'thousand persons', 'total_matches': len(out), 'records': out[:limit], 'country_source_entries': references, 'citation_note': 'Local workbook provenance, edition, units and rights are unverified.' if local_file else 'See source sheets and citation policy: original papers are required for any chart or subsets of fewer than 12 countries.'}
    finally:
        w.close()
