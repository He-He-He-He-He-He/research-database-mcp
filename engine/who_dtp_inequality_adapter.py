"""WHO HIDR 区县五分组的 DTP1-DTP3 接种脱落率数据。"""
import release_runtime
import argparse, io, json, re, subprocess, datetime
import openpyxl
URL = 'https://datasafe-h5afbhf4gwctabaa.z01.azurefd.net/api/download/TOP/rep_dtp_sub/data'

def dtp_dropout(country):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 必须是大写 ISO3 代码')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('WHO HIDR 下载失败')
    if len(p.stdout) > 10000000:
        raise RuntimeError('WHO HIDR 文件超出大小限制')
    wb = openpyxl.load_workbook(io.BytesIO(p.stdout), read_only=True, data_only=True)
    try:
        if 'Data' not in wb.sheetnames:
            raise RuntimeError('WHO HIDR 表格结构变更')
        rows = wb['Data'].iter_rows(values_only=True)
        headers = next(rows)
        required = {'setting', 'date', 'indicator_name', 'dimension', 'subgroup', 'estimate', 'population', 'flag', 'setting_average', 'iso3', 'source', 'update', 'dataset_id'}
        if not required.issubset(headers):
            raise RuntimeError('WHO HIDR 列结构变更')
        out = []
        for values in rows:
            r = dict(zip(headers, values))
            if r.get('iso3') == country:
                out.append({k: r.get(k).isoformat() if isinstance(r.get(k), (datetime.date, datetime.datetime)) else r.get(k) for k in ('setting', 'date', 'indicator_name', 'dimension', 'subgroup', 'estimate', 'population', 'flag', 'setting_average', 'source', 'update')})
    finally:
        wb.close()
    return {'source': 'WHO Health Inequality Data Repository: Subnational DTP immunization dropout rates (WHO/UNICEF)', 'source_url': URL, 'metadata_url': 'https://www.who.int/data/sets/health-inequality-monitor-dataset#dtp-subnational', 'citation': 'The Health Inequality Data Repository API. Geneva: World Health Organization, 2025. https://www.who.int/data/inequality-monitor/data', 'country': country, 'unit': 'percent', 'scope': '1 岁儿童 DTP 第一剂至第三剂接种脱落率，区县按脱落率分成五分组；各行时间与数据更新日期按源文件返回，不代表当前接种率或个人接种风险。', 'count': len(out), 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('country')
    a = p.parse_args()
    print(json.dumps(dtp_dropout(a.country), ensure_ascii=False, indent=2, default=str))
