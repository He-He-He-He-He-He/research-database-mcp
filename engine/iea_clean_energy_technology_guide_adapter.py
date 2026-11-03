"""IEA's downloadable Clean Energy Technology Guide public CSV."""
import release_runtime
import csv
import io
import subprocess
URL = 'https://www.iea.org/files/57136415-72b6-4548-9deb-f81fc9a6048d/IEACleanTechGuidepublicdataset.csv'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/etp-clean-energy-technology-guide'
LIMIT = 5000000

def _load():
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(LIMIT), URL], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA CSV download failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > LIMIT:
        raise ValueError('IEA CSV too large')
    reader = csv.DictReader(io.StringIO(r.stdout.decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or 'tech.final.name' not in reader.fieldnames or 'TRL.2025' not in reader.fieldnames:
        raise ValueError('unexpected CSV schema')
    rows = list(reader)
    if any((None in row or any((v is None for v in row.values())) for row in rows)):
        raise ValueError('malformed CSV row')
    return rows

def search(keyword='', category='', limit=20, offset=0):
    if any((not isinstance(x, str) or len(x) > 150 for x in (keyword, category))):
        raise ValueError('invalid search')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = _load()
    selected = [r for r in rows if (not keyword or keyword.casefold() in ' '.join(r.values()).casefold()) and (not category or any((category.casefold() in r.get('category.' + str(i), '').casefold() for i in range(1, 5))))]
    return {'source': URL, 'page': PAGE, 'page_updated': '2026-07-24', 'csv_rows': len(rows), 'total': len(selected), 'limit': limit, 'offset': offset, 'rows': selected[offset:offset + limit], 'note': 'Public page says 640 designs; retrieved CSV may differ in count and contains TRL columns through 2025, despite later page update. TRL is an IEA readiness assessment, not measured emissions or deployment. Original text, classifications and empty strings retained; consult IEA methodology and update history.'}
