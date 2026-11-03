"""NASA Earthdata CMR 地球科学数据集合与颗粒元数据检索。"""
import release_runtime
import math, re
import requests
BASE = 'https://cmr.earthdata.nasa.gov/search/'

def search(kind, keyword=None, collection_id=None, bbox=None, temporal=None, page_size=20, page_num=1):
    if kind not in ('collections', 'granules'):
        raise ValueError('kind须为collections或granules')
    if keyword is not None and (not isinstance(keyword, str) or not 1 <= len(keyword) <= 200):
        raise ValueError('keyword无效')
    if collection_id is not None and (not isinstance(collection_id, str) or not re.fullmatch('C[0-9]+-[A-Za-z0-9_]+', collection_id)):
        raise ValueError('集合ID无效')
    if kind == 'granules' and (not collection_id):
        raise ValueError('颗粒检索须指定集合ID')
    if kind == 'collections' and collection_id:
        raise ValueError('集合ID仅用于颗粒检索')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size须为1–100')
    if isinstance(page_num, bool) or not isinstance(page_num, int) or (not 1 <= page_num <= 1000):
        raise ValueError('page_num无效')
    p = {'page_size': page_size, 'page_num': page_num}
    if keyword:
        p['keyword'] = keyword
    if collection_id:
        p['collection_concept_id'] = collection_id
    if temporal:
        if not isinstance(temporal, str) or len(temporal) > 100:
            raise ValueError('temporal无效')
        p['temporal'] = temporal
    if bbox is not None:
        if not isinstance(bbox, (tuple, list)) or len(bbox) != 4 or any((isinstance(v, bool) or not isinstance(v, (int, float)) or (not math.isfinite(v)) for v in bbox)):
            raise ValueError('bbox无效')
        w, s, e, n = bbox
        if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
            raise ValueError('bbox须为西南东北经纬度且不跨反经线')
        p['bounding_box'] = ','.join(map(str, bbox))
    r = requests.get(BASE + kind + '.json', params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    feed = d.get('feed', {})
    if not isinstance(feed.get('entry'), list):
        raise ValueError('非预期CMR响应')
    return {'source': 'NASA Earthdata Common Metadata Repository', 'source_url': r.url, 'kind': kind, 'hits': r.headers.get('CMR-Hits'), 'page_num': page_num, 'entries': feed['entry'], 'note': '返回集合或数据颗粒元数据，不表示遥感文件已下载或有访问权限；个别数据服务需要Earthdata登录。bbox采用WGS84经纬度，时间格式以官方CMR规范为准。'}
