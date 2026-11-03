"""World Bank Business Ready 2025 economy-level topic questionnaire answers."""
import release_runtime
import argparse, datetime, io, json, zipfile, openpyxl, requests
URL = 'https://www.worldbank.org/content/dam/sites/b-ready/documents/excel/B-READY_ALL_DATA_2025.zip'
FILE = '02_B-READY-2025-EconomyAnswer.xlsx'
SHEETS = {'entry': '01_Business_Entry', 'location': '02_Business_Location', 'utilities': '03_Utility_Services', 'labour': '04_Labor', 'finance': '05_Financial_Services', 'trade': '06_International_Trade', 'taxation': '07_Taxation', 'disputes': '08_Dispute_Resolution', 'competition': '09_Market_Competition', 'insolvency': '10_Business_Insolvency'}

def query(country, topic, keyword='', limit=50, local_zip=None):
    if not isinstance(country, str) or not 1 <= len(country) <= 100 or topic not in SHEETS or (not isinstance(keyword, str)) or (len(keyword) > 200) or (not 1 <= limit <= 500):
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
        if info.file_size > 10000000:
            raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(z.read(info)), read_only=True, data_only=True)
        try:
            it = w[SHEETS[topic]].values
            h = next(it)
            if tuple(h[:5]) != ('Economy', 'Technical Variable Name', 'Survey Question Text', 'Economy Response', 'Data Source'):
                raise ValueError('unexpected schema')
            rows = []
            count = 0
            for row in it:
                if not isinstance(row[0], str) or row[0].casefold() != country.casefold() or keyword.casefold() not in (str(row[1]) + ' ' + str(row[2])).casefold():
                    continue
                count += 1
                if len(rows) < limit:
                    rows.append({h[i]: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for i, v in enumerate(row[:5])})
            return {'source': URL, 'dataset': 'Business Ready 2025 economy-level answers', 'topic': topic, 'matched_count': count, 'records': rows, 'note': 'Report-era expert/survey answers, not a current legal opinion; original response and data source are preserved.'}
        finally:
            w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('topic', choices=SHEETS)
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=50)
    p.add_argument('--local-zip')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.topic, a.keyword, a.limit, a.local_zip), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
