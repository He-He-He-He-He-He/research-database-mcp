"""Japanese National Diet Library, official Imperial Diet historical speech search API."""
import release_runtime
import json
import os
import subprocess
from datetime import date
from urllib.parse import urlencode
BASE = 'https://teikokugikai-i.ndl.go.jp/api/emp/speech'
DOC = 'https://teikokugikai-i.ndl.go.jp/teikoku_api.html'

def _date(value):
    if not value:
        return ''
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('日期须为 YYYY-MM-DD') from None
    return value

def search(keyword, start=1, limit=3, date_from='', date_until='', house=''):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(start, bool) or not isinstance(start, int) or start < 1:
        raise ValueError('start 必须为正整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit 须为 1 至 10 的整数')
    date_from, date_until = (_date(date_from), _date(date_until))
    if date_from and date_until and (date_from > date_until):
        raise ValueError('开始日期不能晚于结束日期')
    if house not in ('', '衆議院', '貴族院'):
        raise ValueError('院别须为衆議院或貴族院')
    params = {'any': keyword, 'startRecord': start, 'maximumRecords': limit, 'recordPacking': 'json'}
    if date_from:
        params['from'] = date_from
    if date_until:
        params['until'] = date_until
    if house:
        params['nameOfHouse'] = house
    proxy = release_runtime.environment.get('JAPAN_IMPERIAL_DIET_PROXY', '')
    command = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30']
    if proxy:
        command += ['--proxy', proxy]
    command += [BASE + '?' + urlencode(params)]
    response = release_runtime.run(command, capture_output=True, timeout=35)
    if response.returncode:
        raise RuntimeError('日本帝国议会会议录查询失败，请核查本机代理和网络')
    try:
        data = json.loads(response.stdout)
        total = data['numberOfRecords']
        records = data.get('speechRecord', [] if total == 0 else None)
        if not isinstance(records, list) or not isinstance(total, int):
            raise ValueError('bad schema')
        items = [{key: record.get(key) for key in ('speechID', 'issueID', 'session', 'nameOfHouse', 'nameOfMeeting', 'issue', 'date', 'speechOrder', 'speaker', 'speakerPosition', 'speakerGroup', 'speech', 'speechURL', 'meetingURL')} for record in records]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('日本帝国议会会议录接口返回结构异常') from exc
    return {'source': '日本国立国会图书馆帝国议会历史会议录搜索 API', 'documentation': DOC, 'keyword': keyword, 'date_from': date_from or None, 'date_until': date_until or None, 'house': house or None, 'total': data['numberOfRecords'], 'start': data.get('startRecord'), 'next': data.get('nextRecordPosition'), 'items': items, 'scope': '官方帝国议会历史会议录发言及会议信息，覆盖 1890—1947 年；不是战后国会、Westlaw Japan 商业库、司法判例或现行法律。OCR 文字可能有误，请核对原始会议录。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--from-date', default='')
    p.add_argument('--until-date', default='')
    p.add_argument('--house', choices=['', '衆議院', '貴族院'], default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.start, a.limit, a.from_date, a.until_date, a.house), ensure_ascii=False, indent=2))
