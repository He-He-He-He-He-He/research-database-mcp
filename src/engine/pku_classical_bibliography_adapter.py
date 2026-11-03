"""Single public query of PKU's 经籍指掌 classical bibliographies."""
import release_runtime
import requests
API = 'https://bib.pkudh.org/api/get_statistic'
PROJECT = 'https://pkudh.org/project/bib/'
SITE = 'https://bib.pkudh.org/statistic'
SCOPE = '北大数字人文研究中心与中科院自然科学史所的独立目录分析系统，涵盖九种目录，其中部分目录与浙大“阅藏知津”资源使用共同底本；不是该馆藏产品或古籍全文。服务器会返回匹配的完整结果，本工具仅展示前 limit 条；个别书目及分类须依原始著录核验。'

def search(keyword, limit=10, exact=False, traditional=True):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 80:
        raise ValueError('关键词须为不超过 80 字的非空字符串')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit 须为 1 至 20 的整数')
    if not isinstance(exact, bool) or not isinstance(traditional, bool):
        raise ValueError('匹配和字形选项必须是布尔值')
    response = requests.post(API, json=[0, keyword.strip(), exact, traditional], timeout=40, stream=True)
    response.raise_for_status()
    raw = bytearray()
    with response:
        for chunk in response.iter_content(chunk_size=65536):
            raw.extend(chunk)
            if len(raw) > 8000000:
                raise RuntimeError('站点查询结果超过本机安全读取上限，请缩小关键词')
    import json
    try:
        payload = json.loads(raw)
        if payload.get('error') != 0:
            raise RuntimeError('古籍系统查询失败：' + str(payload.get('message', ''))[:200])
        data = payload['data']
        records = data['book_records']['data']
        statistics = data['statistic_data']
        if not isinstance(records, list) or not isinstance(statistics, list):
            raise ValueError('unexpected response')
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('古籍系统返回结构异常') from exc
    return {'source': '北京大学数字人文研究中心／中国科学院自然科学史研究所经籍指掌', 'source_url': SITE, 'project_description': PROJECT, 'keyword': keyword, 'exact': exact, 'traditional': traditional, 'total': len(records), 'limit': limit, 'items': records[:limit], 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--exact', action='store_true')
    p.add_argument('--simplified', action='store_true')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit, a.exact, not a.simplified), ensure_ascii=False, indent=2))
