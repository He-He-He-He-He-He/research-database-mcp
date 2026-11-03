"""WRI Global Power Plant Database v1.3.0 (June 2021), official historical release."""
import release_runtime
import csv, io, re, zipfile
import requests
URL = 'https://datasets.wri.org/private-admin/dataset/53623dfd-3df6-4f15-a091-67457cdb571f/resource/66bcdacc-3d0e-46ad-9271-a5a76b1853d2/download/globalpowerplantdatabasev130.zip'
SOURCE = 'https://datasets.wri.org/datasets/global-power-plant-database'
NOTE = 'WRI v1.3.0 historical release (June 2021), a multi-source compilation, not a current or comprehensive operating-plant inventory. Capacity is MW; annual generation is GWh. Reported and model-estimated fields are separate and may use calendar or fiscal years. Blank fields are missing, not zero. Fuel, ownership, operating status and dates require original-source checks. Other-fuel ordering is not priority. Country codes, location and plant source are original. Do not infer national total generation or current CBD electricity supply from these records.'

def _records(session=None):
    response = (session or requests).get(URL, timeout=65)
    response.raise_for_status()
    raw = response.content
    if len(raw) > 12000000:
        raise ValueError('archive exceeds size bound')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = 'global_power_plant_database.csv'
        info = z.getinfo(name)
        if info.file_size > 35000000:
            raise ValueError('data exceeds size bound')
        with z.open(info) as f:
            rd = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            required = {'country', 'country_long', 'name', 'gppd_idnr', 'capacity_mw', 'primary_fuel', 'source', 'generation_data_source'}
            if not rd.fieldnames or not required.issubset(rd.fieldnames):
                raise ValueError('unexpected database header')
            rows = []
            for x in rd:
                if None in x or not x['country'] or (not x['gppd_idnr']):
                    raise ValueError('malformed source row')
                rows.append(x)
                if len(rows) > 100000:
                    raise ValueError('unexpected record count')
            return (rows, len(raw))

def search(country, fuel=None, keyword=None, offset=0, limit=20, session=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be ISO3')
    if fuel is not None and (not isinstance(fuel, str) or not fuel.strip() or len(fuel) > 80):
        raise ValueError('invalid fuel')
    if keyword is not None and (not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 120):
        raise ValueError('invalid keyword')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    rows, archive_bytes = _records(session)
    country = country.upper()
    items = [x for x in rows if x['country'] == country and (fuel is None or x['primary_fuel'].casefold() == fuel.strip().casefold()) and (keyword is None or keyword.strip().casefold() in x['name'].casefold())]
    return {'country': country, 'primary_fuel': fuel, 'keyword': keyword, 'total': len(items), 'offset': offset, 'limit': limit, 'items': items[offset:offset + limit], 'snapshot': '1.3.0 (June 2021)', 'source': SOURCE, 'archive_url': URL, 'archive_bytes': archive_bytes, 'licence': 'Creative Commons Attribution (CC BY)', 'note': NOTE}
