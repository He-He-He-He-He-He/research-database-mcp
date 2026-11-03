"""USDA FoodData Central public food search and food nutrient detail."""
import release_runtime
import os
import requests
BASE = 'https://api.nal.usda.gov/fdc/v1'
DOC = 'https://fdc.nal.usda.gov/api-guide/'
MAX = 8000000

def _get(path, params):
    key = release_runtime.environment.get('USDA_FDC_API_KEY') or 'DEMO_KEY'
    try:
        r = requests.get(BASE + path, params={**params, 'api_key': key}, timeout=30, stream=True)
        if r.status_code != 200:
            raise RuntimeError('USDA API HTTP ' + str(r.status_code))
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > MAX:
                raise ValueError('USDA response exceeds size limit')
            parts.append(b)
    except requests.RequestException as e:
        raise RuntimeError('USDA API connection failed') from None
    import json
    obj = json.loads(b''.join(parts))
    if not isinstance(obj, dict):
        raise ValueError('unexpected response')
    return obj

def search(query, page=1, per_page=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 150:
        raise ValueError('invalid query')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, per_page))) or page < 1 or (not 1 <= per_page <= 50):
        raise ValueError('invalid pagination')
    data = _get('/foods/search', {'query': query, 'pageNumber': page, 'pageSize': per_page})
    if not isinstance(data.get('foods'), list) or not isinstance(data.get('totalHits'), int):
        raise ValueError('unexpected search response')
    return {'source': BASE + '/foods/search', 'documentation': DOC, 'request': {'query': query, 'page': page, 'per_page': per_page}, 'response': data, 'note': 'USDA search results span different data types and products; match food, preparation and serving basis before comparison. Retains raw nutrient amounts and units. Source CC0. Demo key shares low IP rate limits; configure USDA_FDC_API_KEY for regular use. Not individualized medical advice.'}

def food(fdc_id):
    if isinstance(fdc_id, bool) or not isinstance(fdc_id, int) or (not 1 <= fdc_id <= 999999999):
        raise ValueError('invalid FDC ID')
    data = _get('/food/' + str(fdc_id), {})
    if data.get('fdcId') != fdc_id:
        raise ValueError('unexpected food ID')
    return {'source': BASE + '/food/' + str(fdc_id), 'documentation': DOC, 'response': data, 'note': 'USDA FoodData Central entry retains original nutrient units, basis, publication and data type; food composition varies by sample and preparation. Verify serving/measurement basis before comparison. Source CC0. Demo key has shared low rate limits; not individualized medical advice.'}
