"""Brazil central bank SGS series 432: COPOM Selic target, annual percent."""
import release_runtime
import argparse
from datetime import datetime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados'

def selic_target(start_date, end_date):
    try:
        start, end = (datetime.strptime(x, '%Y-%m-%d').date() for x in (start_date, end_date))
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYY-MM-DD') from None
    if start > end or (end - start).days > 3652:
        raise ValueError('date range must be ordered and at most 10 years')
    params = {'formato': 'json', 'dataInicial': start.strftime('%d/%m/%Y'), 'dataFinal': end.strftime('%d/%m/%Y')}
    url = BASE + '?' + urlencode(params)
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    rows = json.loads(proc.stdout)
    if not isinstance(rows, list):
        raise ValueError('unexpected BCB response')
    for row in rows:
        try:
            day = datetime.strptime(row['data'], '%d/%m/%Y').date()
            float(row['valor'])
        except (KeyError, TypeError, ValueError):
            raise ValueError('invalid BCB observation') from None
        if not start <= day <= end:
            raise ValueError('BCB observation outside requested period')
    return {'source': 'Banco Central do Brasil, SGS series 432', 'indicator': 'COPOM Selic target rate', 'unit': 'percent per year', 'frequency': 'daily', 'start_date': start_date, 'end_date': end_date, 'source_url': url, 'observations': rows, 'license': 'ODbL', 'note': 'Policy target, not the observed overnight Selic rate; values are annualized percentage points.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('start_date')
    p.add_argument('end_date')
    a = p.parse_args()
    print(json.dumps(selic_target(a.start_date, a.end_date), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
