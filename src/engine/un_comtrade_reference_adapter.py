"""UN Comtrade official public reporter and commodity reference codes."""
import release_runtime
import json, requests
BASE = 'https://comtradeapi.un.org/files/v1/app/reference/'
SETS = {'reporters': ('Reporters.json', '报告经济体'), 'hs': ('HS.json', '综合 HS'), 'hs2022': ('H6.json', 'HS 2022')}

def search(kind, keyword='', limit=20, offset=0):
    if kind not in SETS:
        raise ValueError('类别须为 reporters、hs 或 hs2022')
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 100000):
        raise ValueError('分页范围无效')
    filename, label = SETS[kind]
    url = BASE + filename
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('参考目录发生跳转')
        r.raise_for_status()
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 5000000:
                raise ValueError('参考文件过大')
            chunks.append(chunk)
        modified = r.headers.get('Last-Modified')
    obj = json.loads(b''.join(chunks))
    items = obj.get('results') if isinstance(obj, dict) else None
    if not isinstance(items, list):
        raise RuntimeError('参考目录结构异常')
    term = keyword.casefold().strip()
    found = [x for x in items if isinstance(x, dict) and term in ' '.join((str(x.get(k, '')) for k in ('id', 'text', 'reporterCode', 'reporterDesc', 'reporterCodeIsoAlpha2', 'reporterCodeIsoAlpha3'))).casefold()]
    return {'source_url': url, 'server_last_modified': modified, 'kind': kind, 'classification': label, 'upstream_metadata': {k: v for k, v in obj.items() if k != 'results'}, 'keyword': keyword, 'directory_count': len(items), 'matched': len(found), 'offset': offset, 'returned': len(found[offset:offset + limit]), 'items': found[offset:offset + limit], 'note': '关键词在本次下载的当前官方参考文件内本地匹配，目录可能更新；经济体列表不保证可作为所有年份的报告方或伙伴方。商品代码保留层级、版本与单位标志，父子类别不可相加；实际数据按报告方、年份、贸易流和分类另行查询。公开预览最多 500 行，不是完整下载，历史值可能修订。'}
