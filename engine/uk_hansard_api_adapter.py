"""UK Parliament Hansard official spoken-contribution search API."""
import release_runtime
from datetime import date
import requests
URL = 'https://hansard-api.parliament.uk/search/contributions/Spoken.json'
DOC = 'https://hansard-api.parliament.uk/swagger/ui/index#!/Search/Search_SearchContributions'

def _date(value):
    if not value:
        return ''
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('日期须为 YYYY-MM-DD') from None
    return value

def search(keyword, limit=3, offset=0, date_from='', date_until=''):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit 须为 1 至 10 的整数')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset 须为 0 至 10000 的整数')
    date_from, date_until = (_date(date_from), _date(date_until))
    if date_from and date_until and (date_from > date_until):
        raise ValueError('开始日期不能晚于结束日期')
    params = {'searchTerm': keyword, 'take': limit, 'skip': offset}
    if date_from:
        params['startDate'] = date_from
    if date_until:
        params['endDate'] = date_until
    response = requests.get(URL, params=params, timeout=45)
    response.raise_for_status()
    try:
        data = response.json()
        rows = data['Results']
        total = data['TotalResultCount']
        if not isinstance(rows, list) or not isinstance(total, int):
            raise ValueError('bad schema')
        fields = ('MemberName', 'MemberId', 'AttributedTo', 'ContributionExtId', 'ContributionText', 'ContributionTextFull', 'DebateSection', 'DebateSectionExtId', 'SittingDate', 'House')
        items = [{field: r.get(field) for field in fields} for r in rows]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('英国议会 Hansard API 返回结构异常') from exc
    return {'source': '英国议会 Hansard 官方口头发言接口', 'source_url': response.url, 'documentation': DOC, 'keyword': keyword, 'date_from': date_from or None, 'date_until': date_until or None, 'total': total, 'offset': offset, 'items': items, 'scope': '英国议会经过编辑的议事发言记录；不是法律现行文本、议案最终表决或法庭判决。发言原文可能包含 HTML 标记。'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--from-date', default='')
    p.add_argument('--until-date', default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit, a.offset, a.from_date, a.until_date), ensure_ascii=False, indent=2))
