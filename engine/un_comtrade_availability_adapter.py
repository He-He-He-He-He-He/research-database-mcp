"""UN Comtrade public goods data availability by reporting economy and period."""
import release_runtime
import re, requests
BASE = 'https://comtradeapi.un.org/public/v1/getDA/C/'
DOC = 'https://uncomtrade.org/docs/data-availability/'

def availability(reporter, period):
    if not isinstance(reporter, str) or not re.fullmatch('\\d{1,3}', reporter):
        raise ValueError('报告经济体须为 1–3 位数字代码')
    if not isinstance(period, str) or not re.fullmatch('\\d{4}(?:\\d{2})?', period):
        raise ValueError('时期须为 YYYY 或 YYYYMM')
    if len(period) == 6 and (not 1 <= int(period[4:]) <= 12):
        raise ValueError('月份须为 01–12')
    freq = 'A' if len(period) == 4 else 'M'
    url = BASE + freq + '/HS'
    with requests.get(url, params={'reporterCode': reporter, 'period': period}, timeout=25, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('上游入口发生跳转')
        if r.status_code == 429:
            raise RuntimeError('UN Comtrade 限流，请稍后低频重试')
        r.raise_for_status()
        parts = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 2000000:
                raise ValueError('响应过大，请缩小查询')
            parts.append(chunk)
        source = r.url
    import json
    j = json.loads(b''.join(parts))
    rows = j.get('data') if isinstance(j, dict) else None
    if not isinstance(rows, list) or type(j.get('count')) is not int or j['count'] != len(rows):
        raise RuntimeError('可用性响应结构或数量异常')
    for row in rows:
        if str(row.get('reporterCode')) != str(int(reporter)) or str(row.get('period')) != period:
            raise RuntimeError('上游返回不符合选择的数据')
        if isinstance(row.get('datasetCode'), int):
            row['datasetCodeExact'] = str(row['datasetCode'])
    return {'source_url': source, 'documentation': DOC, 'reporter': reporter, 'period': period, 'frequency': freq, 'count': j['count'], 'records': rows, 'note': '仅查询当前商品贸易 HS 可用性，记录数是数据集规模而非预览完整度。首次发布时间不证明当前最近修订版在当时可得；核对 firstReleased、lastReleased、分类及原始/转换标记。空列表不代表贸易为零；大整数数据集编号另附精确字符串。公开预览最多 500 行，服务可能限流。'}
