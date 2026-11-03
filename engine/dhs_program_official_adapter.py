"""DHS Program public survey indicator API, retaining survey metadata and uncertainty."""
import release_runtime
import re, requests
BASE = 'https://api.dhsprogram.com/rest/dhs/'
DOC = 'https://api.dhsprogram.com/html/api-data.cfm'
CITATION = 'The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program. ICF. Originally funded by the United States Agency for International Development (USAID). Available from api.dhsprogram.com.'

def _page(x, name):
    if not isinstance(x, int) or isinstance(x, bool) or x < 1 or (name == 'perpage' and x > 100):
        raise ValueError('Invalid ' + name)
    return x

def _get(endpoint, params):
    with requests.get(BASE + endpoint, params=params, timeout=(15, 35), stream=True) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 5000000:
                raise RuntimeError('DHS response too large')
            parts.append(b)
    import json
    x = json.loads(b''.join(parts))
    if not isinstance(x, dict) or not isinstance(x.get('Data'), list) or 'RecordCount' not in x or ('Page' not in x):
        raise RuntimeError('Unexpected DHS response')
    return x

def catalogue(kind, page=1, perpage=20, keyword=''):
    if kind not in ('indicators', 'countries', 'surveys'):
        raise ValueError('Unknown catalogue')
    _page(page, 'page')
    _page(perpage, 'perpage')
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('Invalid keyword')
    x = _get(kind, {'f': 'json', 'page': page, 'perpage': perpage})
    rows = x['Data']
    if keyword:
        rows = [r for r in rows if keyword.casefold() in str(r).casefold()]
    return {'source': 'The Demographic and Health Surveys Program (DHS), ICF', 'documentation': DOC, 'citation': CITATION, 'keyword_scope': 'Only this server page is searched; no claim of complete keyword results', 'server_metadata': {k: v for k, v in x.items() if k != 'Data'}, 'items': rows}

def data(country, indicator, page=1, perpage=20, breakdown='national'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
        raise ValueError('Country is a two-letter DHS country code')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_]{4,40}', indicator):
        raise ValueError('Invalid DHS indicator code')
    _page(page, 'page')
    _page(perpage, 'perpage')
    if breakdown not in ('national', 'subnational', 'background', 'all'):
        raise ValueError('Invalid breakdown')
    x = _get('data', {'f': 'json', 'countryIds': country, 'indicatorIds': indicator, 'breakdown': breakdown, 'page': page, 'perpage': perpage})
    if any((row.get('DHS_CountryCode') != country or row.get('IndicatorId') != indicator for row in x['Data'])):
        raise RuntimeError('DHS returned records outside requested filters')
    return {'source': 'The Demographic and Health Surveys Program (DHS), ICF', 'documentation': DOC, 'citation': CITATION, 'request': {'country': country, 'indicator': indicator, 'breakdown': breakdown}, 'server_metadata': {k: v for k, v in x.items() if k != 'Data'}, 'items': x['Data'], 'note': 'Survey estimates, not current census counts. Survey year, target population, denominator, units, categories and confidence bounds require indicator and survey metadata; national and subgroups overlap. Empty results are not zero.'}

def indicator_metadata(indicator):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_]{4,40}', indicator):
        raise ValueError('Invalid DHS indicator code')
    x = _get('indicators', {'f': 'json', 'indicatorIds': indicator, 'page': 1, 'perpage': 100})
    if any((r.get('IndicatorId') != indicator for r in x['Data'])) or x.get('TotalPages') not in (0, 1):
        raise RuntimeError('Unexpected DHS indicator metadata')
    return {'citation': CITATION, 'documentation': DOC, 'items': x['Data']}

def survey_metadata(survey):
    if not isinstance(survey, str) or not re.fullmatch('[A-Z0-9]{6,40}', survey):
        raise ValueError('Invalid DHS survey identifier')
    x = _get('surveys', {'f': 'json', 'surveyIds': survey, 'page': 1, 'perpage': 100})
    if any((r.get('SurveyId') != survey for r in x['Data'])) or x.get('TotalPages') not in (0, 1):
        raise RuntimeError('Unexpected DHS survey metadata')
    return {'citation': CITATION, 'documentation': DOC, 'items': x['Data']}
