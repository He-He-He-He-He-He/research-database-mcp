"""World Bank historical academic data-use country scores (sample based)."""
import release_runtime
import csv, io, re, subprocess
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0065200/2/DR0092803/data_use_country_scores_annual.csv'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0065200/data-use-in-academia-dataset'

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2000 <= start <= end <= 2020:
        raise ValueError('years must be 2000–2020')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '50', '--max-filesize', '8000000', URL], capture_output=True, timeout=55)
    if p.returncode:
        raise RuntimeError('download failed: ' + p.stderr.decode('utf-8', 'replace')[:300])
    if len(p.stdout) > 8000000:
        raise ValueError('file exceeds 8 MB')
    reader = csv.DictReader(io.StringIO(p.stdout.decode('utf-8-sig'), newline=''))
    if not {'date', 'iso3c', 'papers', 'data_papers', 'country'}.issubset(reader.fieldnames or []):
        raise ValueError('unexpected CSV headers')
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError('duplicate CSV headers')
    rows = [r for r in reader if r['iso3c'] == country.upper() and r['date'].isdigit() and (start <= int(r['date']) <= end)]
    return {'source': URL, 'catalog': CATALOG, 'country': country.upper(), 'records': rows, 'note': '2000–2020 historical sample of English-language Semantic Scholar papers; restricted academic fields, parsable full text and abstracts, convenience sample and machine-classified data use. Counts are not all papers or complete national research output; estimates and 3-year fields differ from raw sampled counts. One article may refer to several countries, so countries overlap. Raw NA, -99 and imputation tags are retained without interpretation or conversion; linked external indicator units and source vintages vary.'}
