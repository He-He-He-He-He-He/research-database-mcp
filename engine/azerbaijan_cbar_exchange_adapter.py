"""Central Bank of Azerbaijan historical official FX bulletin (XML)."""
import release_runtime
import argparse, datetime, json, re, xml.etree.ElementTree as ET
import requests

def rates(date, currency=None):
    try:
        d = datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError('date must be ISO YYYY-MM-DD')
    if currency is not None and (not re.fullmatch('[A-Za-z]{3}', currency)):
        raise ValueError('currency must be a three-letter code')
    url = 'https://cbar.az/currencies/' + d.strftime('%d.%m.%Y') + '.xml'
    with requests.get(url, timeout=25, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}, allow_redirects=False) as r:
        r.raise_for_status()
        chunks = []
        n = 0
        for part in r.iter_content(65536):
            n += len(part)
            if n > 2000000:
                raise ValueError('response too large')
            chunks.append(part)
        root = ET.fromstring(b''.join(chunks))
    if root.tag != 'ValCurs':
        raise ValueError('unexpected response')
    result = []
    for group in root.findall('ValType'):
        for v in group.findall('Valute'):
            if currency and v.get('Code', '').upper() != currency.upper():
                continue
            result.append({'code': v.get('Code'), 'group': group.get('Type'), 'nominal': v.findtext('Nominal'), 'name': v.findtext('Name'), 'azn_value': v.findtext('Value')})
    return {'source': url, 'bulletin_date': root.get('Date'), 'description': root.get('Description'), 'rates': result, 'note': 'AZN value corresponds to the stated nominal units; gold/metals use troy ounces, not ordinary currency units.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('date')
    p.add_argument('--currency')
    a = p.parse_args()
    print(json.dumps(rates(a.date, a.currency), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
