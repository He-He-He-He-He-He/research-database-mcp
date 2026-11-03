"""World Bank Global Sugar-Sweetened Beverage Tax Database, August 2023 snapshot."""
import release_runtime
import csv, io, re, subprocess
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0063310/DR0092738/SSB-Tax-Database-Aug23.csv'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0063310/global-ssb-tax-database'

def query(country):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be a three-letter code')
    country = country.upper()
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', '2000000', URL], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('World Bank download failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 2000000:
        raise ValueError('response too large')
    reader = csv.reader(io.StringIO(r.stdout.decode('utf-8-sig'), newline=''))
    headers = next(reader, [])
    if not {'jurisdiction', 'country_code', 'unique_id', 'rate', 'date_imp', 'legislation'}.issubset(headers):
        raise ValueError('unexpected World Bank CSV headers')
    out = []
    for row in reader:
        if len(row) != len(headers):
            raise ValueError('unexpected row length')
        if row[headers.index('country_code')].upper() == country:
            out.append({'columns': headers, 'values': row})
    return {'source': URL, 'catalog': CATALOG, 'snapshot': 'August 2023', 'country_code': country, 'count': len(out), 'records': out, 'note': 'Historical snapshot, last updated August 2023; catalog says no further updates planned. National, subnational and city jurisdictions are separate. Taxes may have changed since the snapshot; consult current legislation. Rate is source text with varying bases and units, not a harmonized numeric rate; preserve N/A and N/I. Empty results do not establish absence of tax. Blank original headers and values are retained in aligned arrays.'}
