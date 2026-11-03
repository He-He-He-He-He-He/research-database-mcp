"""台湾地区观光部门历年旅游统计官方 CSV。"""
import release_runtime
import csv
import io
import requests
TABLES = {'arrivals': ('12', '历年来台旅客统计', '7322'), 'nationality': ('11', '历年来台旅客国籍统计', '45537'), 'residence': ('7', '历年来台旅客居住地统计', '15453'), 'purpose': ('6', '历年来台旅客来台目的统计', '45512'), 'sex': ('8', '历年来台旅客性别统计', '38122'), 'transport': ('13', '历年来台旅客交通工具及入境港口统计', '8359'), 'next_destination': ('16', '历年来台旅客离台后前往地区统计', '15450')}

def catalog():
    return [{'table': k, 'name': v[1], 'dataset_url': 'https://data.gov.tw/dataset/' + v[2]} for k, v in TABLES.items()]

def query(table, keyword='', offset=0, limit=100):
    if table not in TABLES:
        raise ValueError('未知统计表')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不能超过100字')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('offset 须非负，limit 须为 1 至 500')
    ident, title, dataset = TABLES[table]
    url = 'https://stat.taiwan.net.tw/data/opendata/' + ident
    with requests.get(url, timeout=30, allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise RuntimeError('官网发生重定向')
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8000000:
                raise RuntimeError('官方文件超过大小上限')
            chunks.append(c)
    try:
        raw = b''.join(chunks).decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(raw)))
    except (UnicodeError, csv.Error) as e:
        raise RuntimeError('官方 CSV 解析失败') from e
    if not rows or not rows[0] or len(set(rows[0])) != len(rows[0]) or any((len(x) != len(rows[0]) for x in rows)):
        raise RuntimeError('官方 CSV 表头或行列数异常')
    records = [dict(zip(rows[0], row)) for row in rows[1:] if not keyword or keyword.casefold() in ' '.join(row).casefold()]
    return {'source': '台湾地区交通部门观光统计', 'title': title, 'table': table, 'url': url, 'dataset_url': 'https://data.gov.tw/dataset/' + dataset, 'fields': rows[0], 'total_matched': len(records), 'offset': offset, 'limit': limit, 'items': records[offset:offset + limit], 'note': '每次读取官网完整当前 CSV 后本地筛选和分页；各表年份和统计口径不同，原始字符串中的逗号、百分比和缺失标记未转换。数据发布日不等于最新数据年份。'}
