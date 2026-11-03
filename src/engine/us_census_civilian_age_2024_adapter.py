"""U.S. Census Vintage 2024 state civilian population, age and sex."""
import release_runtime
import csv, io, subprocess
URL = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/state/asrh/sc-est2024-agesex-civ.csv'
LAYOUT = 'https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2024/SC-EST2024-AGESEX-CIV.pdf'
SEX = {'0': 'total', '1': 'male', '2': 'female'}

def find(geography, sex='0', age='999', year=2024, limit=10):
    if not isinstance(geography, str) or not geography.strip() or len(geography) > 80:
        raise ValueError('geography is required')
    sex = str(sex)
    age = str(age)
    if sex not in SEX or age not in [str(i) for i in range(86)] + ['999'] or year not in range(2020, 2025):
        raise ValueError('Invalid sex, age, or year')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '30', '--max-filesize', '2000000', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Census download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 2000000:
        raise RuntimeError('CSV too large')
    reader = csv.DictReader(io.StringIO(p.stdout.decode('utf-8-sig')))
    required = {'SUMLEV', 'STATE', 'NAME', 'SEX', 'AGE', f'POPEST{year}_CIV'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise RuntimeError('Unexpected CSV schema')
    result = []
    for row in reader:
        if row['NAME'].casefold() != geography.strip().casefold() or row['SEX'] != sex or row['AGE'] != age:
            continue
        result.append({'geography': row['NAME'], 'state_code': row['STATE'], 'sex_code': sex, 'sex_label': SEX[sex], 'age_code': age, 'age_label': 'total' if age == '999' else '85 and older' if age == '85' else age, 'reference_date': str(year) + '-07-01', 'estimate_persons': row[f'POPEST{year}_CIV'], 'raw_row': row})
    return {'source': 'U.S. Census Bureau, Population Estimates Program', 'dataset_url': URL, 'layout_url': LAYOUT, 'vintage': '2024', 'matched_rows': len(result), 'items': result[:limit], 'note': 'Civilian population excludes Armed Forces and differs from resident population. Age 85 means 85+, 999 total; sex 0 total, 1 male, 2 female. Total and category rows overlap; do not add them. Geographic boundaries as of 2024-01-01; not the latest estimates.'}
