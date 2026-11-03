"""Bounded searches of official State Council policy catalog pages."""
import release_runtime
import datetime, re
from china_data_adapters import policy_search, CATEGORIES

def _date(value):
    if not isinstance(value, str):
        raise ValueError('date must be YYYY-MM-DD')
    try:
        if not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', value):
            raise ValueError()
        datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError('date must be a valid YYYY-MM-DD') from None
    return value

def search(keyword, category='gongwen', field='title', start=None, end=None, issuer='', title_contains='', start_page=1, end_page=3, page_size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or (category not in CATEGORIES) or (field not in ('title', 'content')):
        raise ValueError('invalid query')
    if (start is None) != (end is None):
        raise ValueError('provide start and end dates together')
    if start is not None:
        start = _date(start)
        end = _date(end)
        if start > end:
            raise ValueError('date range is reversed')
    if any((not isinstance(x, str) or len(x) > 100 for x in (issuer, title_contains))):
        raise ValueError('invalid local filter')
    if any((type(x) is not int for x in (start_page, end_page, page_size))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 10 or (not 1 <= page_size <= 20):
        raise ValueError('up to 10 pages, page size 1–20')
    rows = []
    totals = []
    unknown_dates = []
    duplicate = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = policy_search(keyword, page, page_size, category, field)
        items = result.get('items')
        if not isinstance(items, list) or len(items) > page_size:
            raise RuntimeError('unexpected government search page')
        totals.append(result.get('total'))
        for item in items:
            if not isinstance(item, dict):
                raise RuntimeError('invalid search item')
            id = item.get('id')
            marker = id or item.get('url')
            if marker in seen:
                duplicate.append(marker)
            else:
                seen.add(marker)
            if issuer and issuer not in str(item.get('issuer') or ''):
                continue
            if title_contains and title_contains not in str(item.get('title') or ''):
                continue
            if start is not None:
                date = str(item.get('date') or '').replace('.', '-')
                try:
                    _date(date)
                except ValueError:
                    unknown_dates.append(marker)
                    continue
                if not start <= date <= end:
                    continue
            rows.append({'source_page': page, **item})
    return {'source_url': 'https://sousuo.www.gov.cn/zcwjk/', 'query': keyword, 'category': category, 'field': field, 'requested_page_range': [start_page, end_page], 'source_totals': totals, 'local_filters': {'start': start, 'end': end, 'issuer': issuer, 'title_contains': title_contains}, 'matching_rows': len(rows), 'items': rows, 'duplicate_ids': duplicate, 'excluded_missing_date_ids': unknown_dates, 'note': '日期、机关和标题附加条件仅对所选页本地过滤；空结果不代表全库无结果。源列表日期以其标注为准，文件效力及修订须核对官方正文；跨页排序与源数据可能变化。'}
