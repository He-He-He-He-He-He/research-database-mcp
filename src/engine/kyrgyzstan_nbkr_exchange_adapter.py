"""National Bank of Kyrgyz Republic daily and weekly official rates."""
import release_runtime
import argparse, json, re, xml.etree.ElementTree as ET
import requests
BASE = 'https://www.nbkr.kg/XML/'

def rates(period='daily', currency=None):
    if period not in ('daily', 'weekly', 'reference'):
        raise ValueError('period must be daily, weekly or reference')
    if currency is not None and (not re.fullmatch('[A-Za-z]{3}', currency)):
        raise ValueError('invalid currency')
    name = {'daily': 'daily.xml', 'weekly': 'weekly.xml', 'reference': 'CurrenciesReferenceList.xml'}[period]
    url = BASE + name
    with requests.get(url, timeout=25, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 2000000:
                raise ValueError('response too large')
            chunks.append(b)
        root = ET.fromstring(b''.join(chunks))
    if root.tag not in ('CurrencyRates', 'ReferenceList'):
        raise ValueError('unexpected response')
    out = []
    for e in root.findall('Currency'):
        if currency and e.get('ISOCode', '').upper() != currency.upper():
            continue
        out.append({'code': e.get('ISOCode'), 'nominal': e.findtext('Nominal'), 'kgs_value': e.findtext('Value'), 'valid_days': e.findtext('ValidFor')})
    return {'source': url, 'bulletin_date': root.get('Date'), 'period': period, 'rates': out, 'note': 'Rates are KGS per stated nominal units; decimal comma retained. Reference list is not a rate feed.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('period', choices=['daily', 'weekly', 'reference'])
    p.add_argument('--currency')
    a = p.parse_args()
    print(json.dumps(rates(a.period, a.currency), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
