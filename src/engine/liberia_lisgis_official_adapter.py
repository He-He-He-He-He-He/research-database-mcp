"""Read selected public datasets exposed by Liberia's official statistics agency."""
import release_runtime
import requests
DATASETS = ('population-counties', 'population-districts', 'population-clans', 'gdp-total', 'gdp-production', 'gdp-expenditure', 'gdp-sectors', 'cpi-aggregates', 'cpi-changes', 'cpi-item-indices')
BASE = 'https://lisgis.gov.lr/api/datasets/'

def read(dataset, keyword='', offset=0, limit=20, field='', value=''):
    if dataset not in DATASETS:
        raise ValueError('Unknown LISGIS dataset')
    if not isinstance(keyword, str) or len(keyword) > 120 or (not isinstance(field, str)) or (not isinstance(value, str)) or (len(field) > 120) or (len(value) > 120) or (bool(field) != bool(value)) or (not isinstance(offset, int)) or isinstance(offset, bool) or (offset < 0) or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid keyword, offset, or limit')
    url = BASE + dataset
    with requests.get(url, timeout=(15, 40), stream=True) as response:
        response.raise_for_status()
        chunks, size = ([], 0)
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 5000000:
                raise RuntimeError('LISGIS dataset exceeds 5 MB')
            chunks.append(chunk)
    import json
    doc = json.loads(b''.join(chunks))
    if not isinstance(doc, dict) or doc.get('id') != dataset or (not isinstance(doc.get('rows'), list)) or (not all((isinstance(row, dict) for row in doc['rows']))):
        raise RuntimeError('Unexpected LISGIS dataset response')
    rows = doc.pop('rows')
    if field and (not any((field in row for row in rows))):
        raise ValueError('Field absent from LISGIS records')
    needle = keyword.casefold().strip()
    matching = [r for r in rows if (not needle or needle in json.dumps(r, ensure_ascii=False).casefold()) and (not field or str(r.get(field)) == value)]
    return {'source_url': url, 'license_page': 'https://lisgis.gov.lr/open-data-license', 'metadata': doc, 'total_rows': len(rows), 'matched_rows': len(matching), 'offset': offset, 'items': matching[offset:offset + limit], 'note': 'Rows filtered locally; consult metadata measures, source and license. 2022 census records are historical. County data for Lofa (21) have an upstream discrepancy: population 367376, male 183063, female 184238; original values retained without correction.'}
