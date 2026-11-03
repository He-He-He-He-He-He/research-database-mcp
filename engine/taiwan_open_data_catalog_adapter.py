"""台湾地区政府资料开放平台公开数据集目录 CSV。"""
import release_runtime
import csv
import io
import tempfile
import requests
URL = 'https://data.gov.tw/datasets/export/csv'
FIELDS = ('資料集識別碼', '資料集名稱', '服務分類', '檔案格式', '資料下載網址', '資料集描述', '主要欄位說明', '提供機關', '更新頻率', '授權方式', '相關網址', '計費方式', '上架日期', '詮釋資料更新時間', '資料量')

def search(keyword='', page=1, size=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    if isinstance(size, bool) or not isinstance(size, int) or (not 1 <= size <= 100):
        raise ValueError('每页须为1至100项')
    total = 0
    matched = 0
    items = []
    offset = (page - 1) * size
    with tempfile.TemporaryFile() as tmp:
        with requests.get(URL, stream=True, timeout=(15, 90), allow_redirects=False) as r:
            r.raise_for_status()
            if r.is_redirect:
                raise RuntimeError('官方目录发生重定向')
            amount = 0
            for chunk in r.iter_content(1024 * 1024):
                amount += len(chunk)
                if amount > 100000000:
                    raise RuntimeError('目录超过100MB上限')
                tmp.write(chunk)
        tmp.seek(0)
        with io.TextIOWrapper(tmp, encoding='utf-8-sig', newline='') as text:
            reader = csv.DictReader(text)
            if not reader.fieldnames or not all((k in reader.fieldnames for k in ('資料集識別碼', '資料集名稱', '資料下載網址', '提供機關'))):
                raise RuntimeError('目录表头未识别')
            for row in reader:
                total += 1
                if keyword.casefold() in (row.get('資料集名稱') or '').casefold():
                    matched += 1
                    if offset < matched <= offset + size:
                        items.append({k: row.get(k) for k in FIELDS})
    if total == 0:
        raise RuntimeError('官方目录为空，无法确认是否正常')
    return {'source': '台湾地区政府资料开放平台', 'source_url': URL, 'keyword': keyword, 'catalog_rows': total, 'matched_rows': matched, 'page': page, 'size': size, 'items': items, 'note': '原始 CSV 一行可能对应同一数据集的一项资源，数量是行数而非去重数据集数；本地仅按繁体原文名称匹配。元数据不保证文件可访问，许可、费用及数据时效须核原始发布方。'}
