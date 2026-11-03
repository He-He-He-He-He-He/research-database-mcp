"""World Bank Women, Business and the Law 2026 workbook scores and topic questions."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038489/DR0095939/2026.02.19_WBL26_FINAL_Data_for_Download.xlsx'
TOPICS = {'scores': 'WBL Economy Scores', 'safety': '1. Safety', 'mobility': '2. Mobility', 'work': '3. Work', 'pay': '4. Pay', 'marriage': '5. Marriage', 'parenthood': '6. Parenthood', 'childcare': '7. Childcare', 'entrepreneurship': '8. Entrepreneurship', 'assets': '9. Assets', 'pension': '10. Pension'}

def query(country, topic='scores', year=2026, local_file=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or topic not in TOPICS or (year not in (2024, 2025, 2026)):
        raise ValueError('invalid query')
    if topic != 'scores' and year != 2026:
        raise ValueError('topic tables contain 2026 only')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        if len(r.content) > 10000000:
            raise ValueError('unexpected file size')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        it = w[TOPICS[topic]].values
        next(it)
        codes = next(it)
        if topic == 'scores':
            next(it)
        labels = next(it)
        if tuple(labels[:6]) != ('Economy', 'Economy Code', 'ISO Code', 'Region', 'Income Group', 'Report Year'):
            raise ValueError('unexpected schema')
        result = []
        for row in it:
            if row[2] != country or row[5] != year:
                continue
            values = [{'column': i + 1, 'code': codes[i] if i < len(codes) else None, 'label': label, 'value': row[i]} for i, label in enumerate(labels) if i >= 6 and label is not None]
            result.append({'economy': row[0], 'economy_code': row[1], 'iso_code': row[2], 'region': row[3], 'income_group': row[4], 'report_year': row[5], 'fields': values})
        return {'source': local_file if local_file else URL, 'dataset': None if local_file else 'Women, Business and the Law 2026', 'topic': topic, 'matched_count': len(result), 'records': result, 'note': '2026 report reflects rules as of 2025-10-01; enforcement values measure expert perceptions. Original cells may contain spreadsheet errors.' + (' Local workbook provenance and version are unverified; the report-specific interpretation requires verification.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--topic', choices=TOPICS, default='scores')
    p.add_argument('--year', type=int, choices=[2024, 2025, 2026], default=2026)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.topic, a.year, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
