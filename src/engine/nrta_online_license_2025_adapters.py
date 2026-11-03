"""广电总局信息网络传播视听节目许可目录，2025 年 7 月快照。"""
import release_runtime
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '广电视听持证机构'
SOURCE = 'https://www.nrta.gov.cn/art/2025/7/28/art_3569_56268.html'

def nrta_online_license_2025(keyword='', page=1, page_size=20):
    page = int(page)
    page_size = int(page_size)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码必须大于零，每页 1—100 条')
    rows = json.loads((ROOT / '2025年7月目录.json').read_text(encoding='utf8'))
    if len(rows) != 403 or [r['序号'] for r in rows] != list(range(1, 404)):
        raise ValueError('快照行数或序号异常')
    needle = ''.join(keyword.split()).casefold()
    matched = [r for r in rows if needle in ''.join(r['单位名称'].split()).casefold()]
    return {'source_url': SOURCE, 'cutoff': '2025-07', 'source_total': len(rows), 'filtered_total': len(matched), 'page': page, 'page_size': page_size, 'results': matched[(page - 1) * page_size:page * page_size]}
