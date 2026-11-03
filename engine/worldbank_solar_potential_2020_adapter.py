"""World Bank/Solargis 2020 photovoltaic potential country ranking workbook."""
import release_runtime
import io
import re
import requests
import openpyxl
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038379/1/DR0046831/solargis_pvpotential_countryranking_2020_data.xlsx'
DOC = 'https://globalsolaratlas.info/global-pv-potential-study'
SHEETS = {'country': 'Country indicators', 'monthly': 'Monthly data', 'distribution': 'Summary statistics'}

def query(section, country='', offset=0, limit=20):
    if section not in (*SHEETS, 'glossary', 'about', 'sources'):
        raise ValueError('unknown section')
    if country and (not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country)):
        raise ValueError('country must be ISO3')
    if country and section not in SHEETS:
        raise ValueError('country filter only applies to data tables')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        if section in SHEETS:
            it = w[SHEETS[section]].iter_rows()
            groups = [c.value for c in next(it)]
            headers = [c.value for c in next(it)]
            end = max((i for i, h in enumerate(headers) if h is not None), default=-1) + 1
            groups = groups[:end]
            headers = headers[:end]
            if not headers or headers[0] != 'ISO_A3':
                raise ValueError('unexpected table format')
            found = []
            for cells in it:
                if not cells[0].value:
                    continue
                if country and str(cells[0].value).upper() != country.upper():
                    continue
                found.append({'values': [c.value for c in cells[:end]], 'number_formats': [c.number_format for c in cells[:end]]})
        else:
            sheet = {'glossary': 'Glossary', 'about': 'About', 'sources': 'Data sources'}[section]
            headers = ['A', 'B']
            groups = None
            found = [{'values': [c.value for c in row[:2]]} for row in w[sheet].iter_rows() if any((c.value is not None for c in row[:2]))]
        return {'source': URL, 'documentation': DOC, 'section': section, 'publication_year': 2020, 'unit_notes': 'GHI kWh/m²/day; PVOUT kWh/kWp/day; LCOE USD/kWh; per-column labels and workbook formatting determine interpretation.', 'headers': headers, 'group_headers': groups, 'total_matches': len(found), 'offset': offset, 'limit': limit, 'rows': found[offset:offset + limit], 'notes': ['Long-term solar resource and modelled utility-scale photovoltaic potential, not actual output in 2020 or a site-specific feasibility study.', 'PVOUT Level 1 excludes identifiable physical land obstacles; Level 2 adds exclusions for potentially protected nature and cropland. Consult glossary and methods.', 'Population/GDP inputs use 2018 and HDI 2017; some fields are stored as fractional values with percent format. Preserve number_formats and labels; duplicate summary column names are positional.', 'World Bank/Solargis Global Solar Atlas study, CC BY 4.0 with required source attribution; input layers may have their own conditions.']}
    finally:
        w.close()
