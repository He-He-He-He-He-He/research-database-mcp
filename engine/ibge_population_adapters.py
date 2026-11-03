"""IBGE SIDRA table 6579 estimated resident population for Brazil and states."""
import release_runtime
import argparse
import json
import re
import subprocess
BASE = 'https://apisidra.ibge.gov.br/values/t/6579'

def population(year, state=None):
    if isinstance(year, bool) or not isinstance(year, int) or (not 2001 <= year <= 2100):
        raise ValueError('year must be an integer from 2001 to 2100')
    if state is not None and (not isinstance(state, str) or not re.fullmatch('\\d{2}', state)):
        raise ValueError('state must be a two-digit IBGE state code, or None for Brazil')
    level, code = ('n1', '1') if state is None else ('n3', state)
    url = f'{BASE}/{level}/{code}/v/9324/p/{year}'
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    rows = json.loads(proc.stdout)
    if not isinstance(rows, list) or len(rows) != 2 or (not isinstance(rows[1], dict)):
        raise ValueError('unexpected SIDRA response')
    row = rows[1]
    if row.get('D1C') != code or row.get('D2C') != '9324' or row.get('D3C') != str(year) or (row.get('MN') != 'Pessoas'):
        raise ValueError('SIDRA response does not match requested dimensions')
    return {'source': 'IBGE SIDRA', 'table': '6579', 'variable': '9324', 'year': year, 'geography_code': code, 'geography': row.get('D1N'), 'unit': 'persons', 'value': row.get('V'), 'source_url': url, 'note': 'Estimated resident population, reference date 1 July. Values and revisions follow IBGE; symbols in value indicate unavailable or suppressed data.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int)
    p.add_argument('--state')
    a = p.parse_args()
    print(json.dumps(population(a.year, a.state), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
