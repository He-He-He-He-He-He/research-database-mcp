"""WHO Health Inequality Data Repository 官方通用数据集目录及国家查询。"""
import release_runtime
import argparse, csv, io, json, re, datetime, zipfile
import requests, openpyxl
CATALOG = 'https://srhdpeuwpubsa.blob.core.windows.net/whdh/HIDR/hidr_datasetid.csv'
BASE = 'https://datasafe-h5afbhf4gwctabaa.z01.azurefd.net/api/download/TOP/'
DOC = 'https://www.who.int/data/inequality-monitor/data/hidr-api'

def catalog(keyword='', limit=30):
    if not isinstance(keyword, str) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 200):
        raise ValueError('关键词或 limit 无效')
    r = requests.get(CATALOG, timeout=25)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not reader.fieldnames or not {'dataset_id', 'dataset_name', 'topic_area'}.issubset(reader.fieldnames):
        raise RuntimeError('WHO 目录结构变更')
    rows = list(reader)
    q = keyword.strip().casefold()
    matches = [x for x in rows if q in ' '.join((str(v or '') for v in x.values())).casefold()]
    return {'source': 'WHO Health Inequality Data Repository', 'source_url': CATALOG, 'documentation': DOC, 'matched': len(matches), 'items': matches[:limit], 'scope': 'WHO 官方数据集目录，本地按代码、英文名称或主题筛选；数据集存在不保证特定国家有数据。'}

def query(dataset, country, start=1900, end=2100, keyword='', limit=50):
    if not isinstance(dataset, str) or not re.fullmatch('rep_[a-z0-9_]{1,80}', dataset):
        raise ValueError('dataset 代码无效')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1900 <= start <= end <= 2100 or (not 1 <= limit <= 500) or (not isinstance(keyword, str)):
        raise ValueError('年份、关键词或数量无效')
    official = catalog(dataset, 200)['items']
    if not any((x['dataset_id'] == dataset for x in official)):
        raise ValueError('未在 WHO 官方目录找到此数据集')
    url = BASE + dataset + '/data'
    buf = io.BytesIO()
    size = 0
    with requests.get(url, stream=True, timeout=(10, 30)) as r:
        r.raise_for_status()
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 15000000:
                raise RuntimeError('WHO 数据文件超过 15 MB；请直接使用官方数据下载链接')
            buf.write(chunk)
    buf.seek(0)
    if not zipfile.is_zipfile(buf):
        raise RuntimeError('WHO 数据接口返回空文件或非 Excel 内容；不能视为空结果')
    buf.seek(0)
    wb = openpyxl.load_workbook(buf, read_only=True, data_only=True)
    try:
        sheets = [s for s in wb.sheetnames if s.casefold() == 'data']
        if len(sheets) != 1:
            raise RuntimeError('WHO 数据表结构变更')
        it = wb[sheets[0]].iter_rows(values_only=True)
        headers = next(it)
        if not {'iso3', 'date', 'indicator_name', 'estimate'}.issubset(headers):
            raise RuntimeError('WHO 数据表缺少关键字段')
        found = 0
        out = []
        q = keyword.casefold().strip()
        for values in it:
            row = dict(zip(headers, values))
            year = row.get('date')
            if row.get('iso3') != country or not isinstance(year, (int, float)) or (not start <= year <= end):
                continue
            if q and q not in (str(row.get('indicator_name') or '') + ' ' + str(row.get('indicator_abbr') or '')).casefold():
                continue
            found += 1
            if len(out) < limit:
                out.append({k: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v for k, v in row.items()})
    finally:
        wb.close()
    return {'source': 'WHO Health Inequality Data Repository', 'source_url': url, 'documentation': DOC, 'dataset': dataset, 'country': country, 'matched': found, 'items': out, 'scope': '国家分组数据由 WHO 汇总多种来源，按原表保留指标、分组、调查年份、估计、区间、单位及状态；含义和时间可随数据集变化，比较前核对指标元数据。数据文件最大 15 MB，匹配结果按原表顺序截取。空结果不是零。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('keyword', nargs='?', default='')
    c.add_argument('--limit', type=int, default=30)
    q = s.add_parser('query')
    q.add_argument('dataset')
    q.add_argument('country')
    q.add_argument('--start', type=int, default=1900)
    q.add_argument('--end', type=int, default=2100)
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    v = catalog(a.keyword, a.limit) if a.cmd == 'catalog' else query(a.dataset, a.country, a.start, a.end, a.keyword, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2, default=str))
