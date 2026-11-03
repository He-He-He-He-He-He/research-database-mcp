"""UNEP Ozone Secretariat individual party and substance group consumption table."""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://ozone.unep.org/countries/data-table'
GROUPS = {1: 'A/I - Chlorofluorocarbons (CFCs)', 2: 'A/II - Halons', 3: 'B/I - Other Fully Halogenated CFCs', 4: 'B/II - Carbon Tetrachloride (CTC)', 5: 'B/III - Methyl Chloroform (TCA)', 6: 'C/I - Hydrochlorofluorocarbons (HCFCs)', 7: 'C/II - Hydrobromofluorocarbons (HBFCs)', 8: 'C/III - Bromochloromethane (BCM)', 9: 'E/I - Methyl Bromide (MB)', 10: 'F - Hydrofluorocarbons (HFCs)'}

def consumption(party_id, group=1, start_year=2020, end_year=2024):
    if isinstance(party_id, bool) or not isinstance(party_id, int) or (not 1 <= party_id <= 9999):
        raise ValueError('party_id must be a positive official party identifier')
    if isinstance(group, bool) or group not in GROUPS:
        raise ValueError('unsupported official substance group')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1986 <= start_year <= end_year <= 2100 or end_year - start_year > 20:
        raise ValueError('year range must be valid and at most 21 years')
    params = {'report_type': '0', 'output_type': 'odp-CO2e-tonnes', 'party[]': str(party_id), 'party_grouping': 'individual', 'group[]': str(group), 'period_start': str(start_year), 'period_end': str(end_year), 'group_by': 'group', 'op': 'GENERATE REPORT', 'form_id': 'ozone_country_data_form__report_table_form'}
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    soup = BeautifulSoup(r.content, 'html.parser')
    selected = soup.select_one(f'select[name="party[]"] option[value="{party_id}"]')
    if not selected:
        raise ValueError('Unknown party identifier in official form')
    party = selected.get_text(' ', strip=True)
    tables = soup.select('table')
    if len(tables) != 1:
        raise ValueError('Expected one group table, got %s' % len(tables))
    trs = tables[0].select('tr')
    if not trs:
        raise ValueError('No table rows')
    headers = [x.get_text(' ', strip=True) for x in trs[0].select('th,td')]
    rows = []
    for tr in trs[1:]:
        values = [x.get_text(' ', strip=True) for x in tr.select('th,td')]
        if not values:
            continue
        if len(values) != len(headers):
            raise ValueError('Unexpected table structure')
        if values[0] != party:
            raise ValueError('Unexpected party in source response')
        for key, value in zip(headers[1:], values[1:]):
            if key.isdigit():
                rows.append({'year': int(key), 'value': value or None})
    return {'source_url': r.url, 'party': party, 'party_id': party_id, 'group': GROUPS[group], 'measure': 'Consumption of controlled substances', 'unit': 'ODP tonnes for ODS; CO2-equivalent tonnes for HFCs', 'note': 'Consumption is calculated from production, imports and exports; negative values are reported values. Empty cells are not reported, not zero. EU members report consumption through EU.', 'rows': rows}
