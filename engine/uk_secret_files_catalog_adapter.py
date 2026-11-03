"""英国国家档案馆 Discovery 官方 API：与 Secret Files 相关的九个原始档案系列。"""
import release_runtime
import json
import requests
API = 'https://discovery.nationalarchives.gov.uk/API/search/records'
SERIES = {'hw1': 'HW 1', 'fo1093': 'FO 1093', 'cab56': 'CAB 56', 'cab81': 'CAB 81', 'cab158': 'CAB 158', 'cab159': 'CAB 159', 'cab163': 'CAB 163', 'cab176': 'CAB 176', 'cab301': 'CAB 301'}
SOURCE_INFORMATION = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1481'

def search(keyword, series='hw1', page=1, limit=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词不能为空且不超过 200 字')
    if series not in SERIES:
        raise ValueError('档案系列不在馆方列示的九个系列中')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码必须是 1 至 100 的整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('每页条数必须是 1 至 20 的整数')
    selected = SERIES[series]
    params = {'SearchQuery': keyword, 'RecordSeries': selected, 'DateFrom': '1873-01-01', 'DateTo': '1953-12-31', 'ResultsPageSize': limit, 'Page': page}
    response = requests.get(API, params=params, headers={'Accept': 'application/json', 'User-Agent': 'ZJU Research Toolkit (personal research)'}, timeout=30)
    response.raise_for_status()
    try:
        data = response.json()
        items = data['records']
        if not isinstance(items, list) or not isinstance(data['count'], int):
            raise ValueError('unexpected API response')
        result = []
        for item in items:
            reference = item.get('reference', '')
            if reference != selected and (not reference.startswith(selected + '/')):
                raise ValueError('unexpected record series')
            record_id = item.get('id', '')
            if not record_id or not record_id.isalnum():
                raise ValueError('unexpected record ID')
            result.append({'reference': reference, 'title': item.get('title'), 'description': item.get('description'), 'covering_dates': item.get('coveringDates'), 'archive_url': 'https://discovery.nationalarchives.gov.uk/details/r/' + record_id, 'held_by': item.get('heldBy'), 'closure_status': item.get('closureStatus')})
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('英国国家档案馆 API 返回结构或系列异常') from exc
    return {'source': '英国国家档案馆 Discovery 正式 API', 'api': API, 'keyword': keyword, 'series': selected, 'date_from_filter': '1873-01-01', 'date_to_filter': '1953-12-31', 'page': page, 'limit': limit, 'total': data['count'], 'items': result, 'scope': '英国国家档案馆原始目录中与商业 Secret Files 馆藏相关的九个系列之一；仅检索目录题名和描述，不代表商业馆藏逐条收录、全文在线或浙江大学访问授权。双端日期筛选由档案馆 API 执行，包含与时间范围重叠的档案和跨期系列级目录；具体档案覆盖日期请逐条核对。', 'relationship_source': SOURCE_INFORMATION}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--series', choices=list(SERIES), default='hw1')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.series, a.page, a.limit), ensure_ascii=False, indent=2))
