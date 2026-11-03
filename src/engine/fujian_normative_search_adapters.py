"""福建省人民政府行政规范性文件库公开检索。"""
import release_runtime
import requests
ENDPOINT = 'https://www.fujian.gov.cn/ssp/search/api/apiSearch'

def search(keyword, page=1, field='title'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入 1–200 字关键词')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or (page > 1000):
        raise ValueError('页码须为 1–1000 的整数')
    if field not in ('title', 'fulltext'):
        raise ValueError('field 须为 title 或 fulltext')
    params = {'siteId': '8a28cde27b39c3a7017b4e11850d009c', 'sourceType': 'SSP_XZGFWJ', 'apiName': 'SSP_XZGFWJ', 'keyWord': keyword.strip(), 'sortFiled': '-gentime', 'searchFiled': 'docTitle' if field == 'title' else '', 'isChange': '1', 'fullKey': 'Y', 'isCollapse': 'N', 'page': page, 'datas': 10}
    response = requests.get(ENDPOINT, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data.get('datas'), list) or not isinstance(data.get('page'), dict):
        raise RuntimeError('官方检索响应结构异常')
    return {'source': '福建省人民政府行政规范性文件库', 'query': keyword.strip(), 'field': field, 'page': data['page'], 'search_metadata': data.get('search'), 'items': data['datas'], 'notice': '检索内容及链接来自官方索引，可能重复或含废止通知；doccontent 不保证完整或现行，需核对原文及效力。'}
_DETAIL_DOMAINS = ('fujian.gov.cn', 'fuzhou.gov.cn', 'xm.gov.cn', 'zhangzhou.gov.cn', 'quanzhou.gov.cn', 'sm.gov.cn', 'putian.gov.cn', 'np.gov.cn', 'longyan.gov.cn', 'ningde.gov.cn', 'pingtan.gov.cn')

def detail(url):
    """读取支持的福建官方政府站点 HTML 正文；附件及其他域名不跟随。"""
    from urllib.parse import urlsplit, urljoin
    from bs4 import BeautifulSoup
    if not isinstance(url, str):
        raise ValueError('需要官方正文 URL')
    current = url
    for _ in range(4):
        p = urlsplit(current)
        try:
            valid_port = p.port in (None, 443)
        except ValueError:
            valid_port = False
        host = (p.hostname or '').lower().rstrip('.')
        if p.scheme != 'https' or not valid_port or p.username is not None or (p.password is not None) or (not any((host == d or host.endswith('.' + d) for d in _DETAIL_DOMAINS))):
            raise ValueError('仅支持指定福建省及设区市政府站 HTTPS 链接')
        response = requests.get(current, timeout=20, allow_redirects=False, stream=True)
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get('Location')
            response.close()
            if not location:
                raise RuntimeError('重定向缺少目标')
            current = urljoin(current, location)
            continue
        response.raise_for_status()
        if 'html' not in response.headers.get('Content-Type', '').lower():
            response.close()
            raise ValueError('只读取 HTML 正文，不读取附件')
        raw = bytearray()
        for block in response.iter_content(65536):
            raw.extend(block)
            if len(raw) > 5000000:
                response.close()
                raise ValueError('页面超过大小限制')
        response.close()
        soup = BeautifulSoup(bytes(raw), 'html.parser')
        node = soup.select_one('#detailCont2 .TRS_Editor, .TRS_Editor, #detailCont2, .detailCont, #zoom')
        if node is None:
            raise RuntimeError('未识别官方正文容器，请查原网页')
        text = node.get_text('\n', strip=True)
        if not text:
            raise RuntimeError('正文为空，请查原网页')
        return {'source': '福建官方政府网站', 'url': current, 'title': soup.title.get_text(' ', strip=True) if soup.title else None, 'text': text, 'notice': '原始发布页面，当前效力及附件须另行核对。'}
    raise RuntimeError('重定向次数超限')
