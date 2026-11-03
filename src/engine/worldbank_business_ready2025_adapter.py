"""World Bank Business Ready 2025 report pillar and detailed topic scores."""
import release_runtime
import argparse, io, json, re, zipfile, openpyxl, requests
URL = 'https://www.worldbank.org/content/dam/sites/b-ready/documents/excel/B-READY_ALL_DATA_2025.zip'
FILE = '01_B-READY-2025-PILLAR-TOPIC-SCORES.xlsx'
SHEETS = {'pillars': '00_B-READY_Pillar_Score', 'entry': '01_Business_Entry', 'location': '02_Business_Location', 'utilities': '03_Utility_Services', 'labour': '04_Labor', 'finance': '05_Financial_Services', 'trade': '06_International_Trade', 'taxation': '07_Taxation', 'disputes': '08_Dispute_Resolution', 'competition': '09_Market_Competition', 'insolvency': '10_Business_Insolvency'}

def query(country, topic='pillars', local_zip=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or topic not in SHEETS:
        raise ValueError('invalid query')
    if local_zip:
        z = zipfile.ZipFile(local_zip)
    else:
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        if len(r.content) > 15000000:
            raise ValueError('unexpected archive size')
        z = zipfile.ZipFile(io.BytesIO(r.content))
    with z:
        info = z.getinfo(FILE)
        if info.file_size > 5000000:
            raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(z.read(info)), read_only=True, data_only=True)
        try:
            it = w[SHEETS[topic]].values
            if topic == 'pillars':
                labels = next(it)
            else:
                next(it)
                next(it)
                next(it)
                labels = next(it)
            if labels[0:2] != ('Economy', 'Economy Code'):
                raise ValueError('unexpected schema')
            rows = []
            for row in it:
                if row[1] != country:
                    continue
                rows.append({'economy': row[0], 'code': row[1], 'fields': [{'column': i + 1, 'label': k, 'value': row[i]} for i, k in enumerate(labels) if i >= 2 and k is not None]})
            return {'source': URL, 'dataset': 'Business Ready 2025', 'topic': topic, 'matched_count': len(rows), 'records': rows, 'note': 'Scores assess the specified report dimensions, not a population percentage or overall rank; no match is not zero.'}
        finally:
            w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--topic', choices=SHEETS, default='pillars')
    p.add_argument('--local-zip')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.topic, a.local_zip), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
