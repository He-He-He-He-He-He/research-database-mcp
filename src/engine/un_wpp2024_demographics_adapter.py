"""UN WPP 2024 medium demographic indicators with January 2026 Togo update."""
import release_runtime
import argparse, csv, gzip, io, json, re, tempfile, zipfile
import requests
ROOT = 'https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/'
MAIN = ROOT + 'CSV_FILES/WPP2024_Demographic_Indicators_Medium.csv.gz'
UPDATE = ROOT + 'WPP2024_CSV_files_update.zip'
UNITS = {'TPopulation1July': 'thousands of people', 'TFR': 'births per woman', 'LEx': 'years'}

def _download(url, fp, maxsize):
    with requests.get(url, timeout=(15, 70), stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        total = 0
        for b in r.iter_content(131072):
            total += len(b)
            if total > maxsize:
                raise ValueError('download exceeds limit')
            fp.write(b)
    fp.seek(0)

def query(iso3, start, end):
    if not re.fullmatch('[A-Z]{3}', iso3) or not 1950 <= start <= end <= 2100:
        raise ValueError('invalid ISO3 or years')
    source = UPDATE if iso3 == 'TGO' else MAIN
    with tempfile.TemporaryFile() as fp:
        _download(source, fp, 25 * 1024 * 1024)
        with zipfile.ZipFile(fp) if iso3 == 'TGO' else gzip.GzipFile(fileobj=fp) as container:
            if iso3 == 'TGO':
                info = container.getinfo('WPP2024_Demographic_Indicators_Medium_Update.csv')
                if info.file_size > 1024 * 1024:
                    raise ValueError('update file exceeds limit')
                binary = container.open(info)
            else:
                binary = container
            with io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as text:
                rows = csv.DictReader(text)
                required = {'ISO3_code', 'Location', 'Time', 'Variant', *UNITS}
                if not required.issubset(rows.fieldnames or []):
                    raise ValueError('unexpected source schema')
                result = []
                for row in rows:
                    if row['ISO3_code'] == iso3 and row['Time'].isdigit() and (start <= int(row['Time']) <= end):
                        result.append({k: row[k] for k in ('ISO3_code', 'Location', 'Time', 'Variant', *UNITS)})
    return {'source': source, 'dataset': 'UN WPP 2024 demographic indicators, medium scenario', 'units': UNITS, 'observations': result, 'note': '2024 onward are projections, not observations. Togo uses 19 January 2026 interim updated file; all values remain original strings.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('iso3')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.iso3, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
