"""Cross-check CAPMAS 2024 printed CPI row against current CAPMAS series."""
import release_runtime
import egypt_capmas_statistics_adapter as capmas
import egypt_figures_2024_adapter as figures
INDICATORS = {'index': 2156, 'annual_rate': 2264, 'monthly_rate': 2268}

def _jan(data, year):
    cats = [x for x in data['categories'] if x.get('id') == 3443]
    if len(cats) != 1:
        raise RuntimeError('CAPMAS urban category missing or ambiguous')
    values = [x for x in cats[0]['data'] if x.get('year') == year and x.get('month') == 1]
    if len(values) != 1:
        raise RuntimeError('CAPMAS January observation missing or ambiguous')
    return values[0]

def crosscheck(path):
    printed = figures.inflation_check(path)
    series = {}
    for label, code in INDICATORS.items():
        r = capmas.indicator(13, 32, code, 2022, 2023)
        series[label] = {'indicator': code, 'metadata': r['indicator_metadata'], 'january_2022': _jan(r, 2022), 'january_2023': _jan(r, 2023)}
    p = printed['monthly_rows'][0]

    def same(key):
        try:
            return float(p[key]) == float(series['index']['january_2023']['value'])
        except (KeyError, TypeError, ValueError):
            return None

    def rate_matches(label):
        try:
            return float(p['2023_rate_of_change_percent_as_printed']) == float(series[label]['january_2023']['value'])
        except (KeyError, TypeError, ValueError):
            return None
    return {'source': 'CAPMAS official CPI API and Egypt in Figures 2024 printed snapshot', 'printed': printed, 'api_series': series, 'comparisons': {'printed_jan_2023_index_equals_api': same('2023_cpi_index'), 'printed_jan_2023_rate_equals_api_monthly_rate': rate_matches('monthly_rate'), 'printed_jan_2023_rate_equals_api_annual_rate': rate_matches('annual_rate')}, 'note': '仅核 CAPMAS 城镇2023年1月的当前API和固定2024刊物；API指标将年度同比与月度环比区分，刊物页脚注与所列数值可能冲突。API可能修订，比较结果不能替代CAPMAS正式更正，也不自动判定其他月份。原始值、单位、来源和出版时点均保留。'}
