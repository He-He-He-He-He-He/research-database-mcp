"""Compare official current CAPMAS PPI observations with a fixed printed snapshot."""
import release_runtime
import math
import fitz
import egypt_capmas_statistics_adapter as capmas
import egypt_figures_2024_adapter as figures

def crosscheck(path):
    bounds = [(185, 209), (220, 247), (250, 279), (290, 315), (320, 348)]
    with figures._open_checked(path) as doc:
        if len(doc) != 230:
            raise RuntimeError('Unexpected PDF page count')
        p = doc[146]
        rows = [[p.get_textbox(fitz.Rect(a, y - 0.5, b, y + 9)).strip() for a, b in bounds] for y in (251.2, 452)]
    expected = [['Jan.', '29.7', '313.3', '19.9', '241.5'], ['Dec.', '40.0', '419.2', '28.2', '299.5']]
    if rows != expected:
        raise RuntimeError('Printed PPI table differs from visually reviewed snapshot')
    d = capmas.indicator(13, 87, 5001, 2022, 2023)
    cats = [c for c in d['categories'] if c.get('id') == 210]
    if len(cats) != 1:
        raise RuntimeError('General index category missing or ambiguous')
    observations = {}
    for y in (2022, 2023):
        for m in (1, 12):
            x = [x for x in cats[0]['data'] if x.get('year') == y and x.get('month') == m]
            if len(x) != 1 or isinstance(x[0].get('value'), bool) or (not isinstance(x[0].get('value'), (int, float))) or (not math.isfinite(x[0]['value'])):
                raise RuntimeError('PPI observation missing or ambiguous')
            observations[f'{y}-{m:02d}'] = x[0]
    printed = {'2022-01': rows[0][4], '2022-12': rows[1][4], '2023-01': rows[0][2], '2023-12': rows[1][2]}
    comparisons = {key: {'printed_index': v, 'api_index': observations[key]['value'], 'difference_api_minus_printed': round(observations[key]['value'] - float(v), 8)} for key, v in printed.items()}
    return {'source': 'CAPMAS public PPI API and Egypt in Figures 2024 fixed snapshot', 'source_url': figures.URL, 'printed_sha256': figures.SHA256, 'printed_physical_page': 147, 'printed_page': 129, 'base_as_printed': 'January 2016=100', 'api_indicator': 5001, 'api_indicator_metadata': d['indicator_metadata'], 'api_observations': observations, 'comparisons': comparisons, 'printed_annual_rates_2023': {'january': '29.7', 'december': '40.0'}, 'note': '仅对比2022/2023年1月及12月的全国生产者价格总指数；接口保留更多小数，当前值可能修订。固定原刊2023年1月313.3、当前API约301.338，2022年12月299.5、当前API约286.788；2023年12月419.2与当前API约419.232接近。差异原因未核，可能涉及修订或口径差异，不能擅自更正或假设所有月份一致。原刊同比脚注称对应上年同月；指数不是CBD成本或终端价格。'}
