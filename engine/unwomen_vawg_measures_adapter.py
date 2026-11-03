"""UN Women Global Database on Violence against Women and Girls: measures export."""
import release_runtime
import json
import requests
URL = 'https://data.unwomen.org/data/export-data'

def query(country, year_from, year_to, limit=50):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country name required')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not 1900 <= year_from <= year_to <= 2100 or (not 1 <= limit <= 100):
        raise ValueError('invalid years or limit')
    data = {'tab': 'data', 'dataresult[unstatscountry]': country.strip(), 'dataresult[eff][eff_min]': str(year_from), 'dataresult[eff][eff_max]': str(year_to), 'filterchecked': 'filterdata'}
    with requests.post(URL, data=data, timeout=45, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(5000001, decode_content=True)
    if len(body) > 5000000:
        raise ValueError('response exceeds 5 MB')
    rows = json.loads(body)
    if not isinstance(rows, list) or any((not isinstance(x, dict) for x in rows)):
        raise ValueError('unexpected export response')
    if any((str(x.get('Country', '')).casefold() != country.strip().casefold() for x in rows)):
        raise ValueError('server returned unexpected country; check name and filters')
    return {'source': 'UN Women Global Database on Violence against Women and Girls', 'source_url': 'https://data.unwomen.org/global-database-on-violence-against-women/data-form', 'country': country, 'source_year_filter': [year_from, year_to], 'total_matches': len(rows), 'records': rows[:limit], 'note': 'Measures are not violence prevalence. Date filters can include historical measures that ended within the interval; do not assume current validity. Verify current law against official national sources. Redistribution permissions have not been verified.'}
