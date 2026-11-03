"""WHO HIDR 高血压患者有效治疗覆盖率年龄标准化估计。"""
import release_runtime
import argparse, io, json, re, subprocess, datetime
import openpyxl
URL = 'https://datasafe-h5afbhf4gwctabaa.z01.azurefd.net/api/download/TOP/rep_gho_hc/data'
INDICATOR = 'NCD_HYP_CONTROL_A'

def hypertension_control(country, start=2000, end=2100):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 必须是大写 ISO3 代码')
    if isinstance(start, bool) or isinstance(end, bool) or (not isinstance(start, int)) or (not isinstance(end, int)) or (not 1900 <= start <= end <= 2100):
        raise ValueError('年份范围无效')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('WHO HIDR 下载失败')
    if len(p.stdout) > 10000000:
        raise RuntimeError('WHO HIDR 文件超出大小限制')
    wb = openpyxl.load_workbook(io.BytesIO(p.stdout), read_only=True, data_only=True)
    try:
        matches = [n for n in wb.sheetnames if n.lower() == 'data']
        if len(matches) != 1:
            raise RuntimeError('WHO HIDR 工作表结构变更')
        rows = wb[matches[0]].iter_rows(values_only=True)
        headers = next(rows)
        required = {'setting', 'date', 'indicator_abbr', 'indicator_name', 'dimension', 'subgroup', 'estimate', 'ci_lb', 'ci_ub', 'flag', 'setting_average', 'iso3', 'source', 'update'}
        if not required.issubset(headers):
            raise RuntimeError('WHO HIDR 列结构变更')
        out = []
        for vals in rows:
            r = dict(zip(headers, vals))
            if r.get('iso3') == country and r.get('indicator_abbr') == INDICATOR and isinstance(r.get('date'), int) and (start <= r['date'] <= end):
                out.append({k: r.get(k).isoformat() if isinstance(r.get(k), (datetime.date, datetime.datetime)) else r.get(k) for k in ('setting', 'date', 'indicator_name', 'dimension', 'subgroup', 'estimate', 'ci_lb', 'ci_ub', 'flag', 'setting_average', 'source', 'update')})
    finally:
        wb.close()
    return {'source': 'WHO Health Inequality Data Repository / WHO Global Health Observatory', 'source_url': URL, 'metadata_url': 'https://www.who.int/data/gho/indicator-metadata-registry/imr-details/5659', 'citation': 'The Health Inequality Data Repository API. Geneva: World Health Organization, 2025. https://www.who.int/data/inequality-monitor/data', 'indicator': INDICATOR, 'country': country, 'unit': 'percent', 'scope': '30–79 岁高血压患者中服药且血压控制达标的人口占比，按性别分列，年龄标准化；源于模型估计并非逐年独立调查，非全部成年人占比；区间、旗标和来源更新日期按源数据保留。', 'count': len(out), 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    p.add_argument('--start', type=int, default=2000)
    p.add_argument('--end', type=int, default=2100)
    a = p.parse_args()
    print(json.dumps(hypertension_control(a.country, a.start, a.end), ensure_ascii=False, indent=2, default=str))
