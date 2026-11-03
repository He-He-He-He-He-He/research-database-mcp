"""U.S. Census Bureau Vintage 2024 resident-population estimates, state file."""
import release_runtime
import csv, io, subprocess
SOURCE = 'https://www.census.gov/programs-surveys/popest.html'
URL = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/state/totals/NST-EST2024-ALLDATA.csv'
LAYOUT = 'https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2024/NST-EST2024-ALLDATA.pdf'
REQUIRED = {'SUMLEV', 'STATE', 'NAME', 'ESTIMATESBASE2020', *[f'POPESTIMATE{x}' for x in range(2020, 2025)]}

def find(geography='', year=None, limit=20):
    if not isinstance(geography, str) or len(geography) > 100:
        raise ValueError('geography must be a string of at most 100 characters')
    if year is not None and year not in range(2020, 2025):
        raise ValueError('year must be 2020–2024')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 66):
        raise ValueError('limit must be 1–66')
    r = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '30', '--max-filesize', '1000000', URL], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('US Census download failed: ' + r.stderr.decode('utf-8', 'replace').strip())
    if len(r.stdout) > 1000000:
        raise RuntimeError('US Census CSV too large')
    reader = csv.DictReader(io.StringIO(r.stdout.decode('utf-8-sig')))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise RuntimeError('US Census CSV schema changed')
    data = []
    for row in reader:
        if row['SUMLEV'] not in ('010', '020', '030', '040'):
            raise RuntimeError('Unexpected summary level')
        if geography and geography.casefold() not in (row['NAME'].casefold(), row['STATE']):
            continue
        population = {str(y): row[f'POPESTIMATE{y}'] for y in ([year] if year else range(2020, 2025))}
        data.append({'name': row['NAME'], 'summary_level': row['SUMLEV'], 'state_fips': row['STATE'], 'population_estimate': population, 'raw_row': row})
    return {'source': 'U.S. Census Bureau Population Estimates Program', 'source_page': SOURCE, 'dataset_url': URL, 'layout_url': LAYOUT, 'vintage': '2024', 'reference_date': 'July 1 of each year', 'unit': 'persons', 'matching_rows': len(data), 'items': data[:limit], 'note': 'Vintage 2024 historical estimate, not the latest vintage or decennial census count. USA excludes Puerto Rico; state FIPS is not unique for regional/division rows. Raw fields include 2020 changes for Apr 1–Jul 1; later annual changes cover Jul 1–Jul 1. Preserve signs and consult official layout before comparing components.'}
