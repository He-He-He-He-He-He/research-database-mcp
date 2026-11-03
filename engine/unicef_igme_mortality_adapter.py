"""UN IGME child mortality estimates from UNICEF's public SDMX dataflow.

The figures are estimates per 1,000 live births, not counts of deaths.
"""
import release_runtime
import re
import unicef_sdmx_general_adapter as sdmx
INDICATORS = {'neonatal': 'CME_MRM0', 'infant': 'CME_MRY0', 'under5': 'CME_MRY0T4'}

def query(country, kind, start, end, sex='_T'):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be a three-letter area code')
    if kind not in INDICATORS:
        raise ValueError('unknown mortality indicator')
    if sex not in ('_T', 'F', 'M'):
        raise ValueError('sex must be _T, F, or M')
    country = country.upper()
    indicator = INDICATORS[kind]
    result = sdmx.data('UNICEF', 'CME', '1.0', f'{country}.{indicator}.{sex}._T', start, end)
    for row in result['observations']:
        if any((row.get(k) != v for k, v in {'REF_AREA': country, 'INDICATOR': indicator, 'SEX': sex, 'WEALTH_QUINTILE': '_T'}.items())):
            raise ValueError('unexpected dimensions in UNICEF result')
    result['dataset'] = 'UN IGME child mortality estimates via UNICEF CME dataflow'
    result['indicator_description'] = {'neonatal': 'neonatal mortality rate', 'infant': 'infant mortality rate', 'under5': 'under-five mortality rate'}[kind]
    result['note'] = 'Modeled estimates; retain original UNIT_MEASURE, DATA_SOURCE, OBS_STATUS and uncertainty bounds. Rates are per 1,000 live births when UNIT_MEASURE is D_PER_1000_B; do not interpret as death counts. Age categories overlap and must not be added. Original fields are unchanged.'
    return result
