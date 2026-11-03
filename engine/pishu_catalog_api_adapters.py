"""皮书数据库公开图书与报告题录单页检索。"""
import release_runtime
import time
import requests
from urllib.parse import urlencode, urlsplit
URL = 'https://www.pishu.com.cn/skwx_ps/search/list'
_last_request = 0.0

def pishu_catalog_search(keyword, resource_type='report', page=1, page_size=10, field='all'):
    global _last_request
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    types = {'report': 'Literature', 'book': 'Book', 'figure': 'ImageTable', 'video': 'Video', 'news': 'News'}
    if resource_type not in types:
        raise ValueError('资源类型须为 report、book、figure、video 或 news')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 10):
        raise ValueError('页码须大于零，每页1至10条')
    fields = {'all': 'All', 'title': 'searchTitle', 'author': 'authors', 'keywords': 'keyWords', 'summary': 'summary', 'subject': 'subjectWords'}
    if field not in fields:
        raise ValueError('字段须为 all、title、author、keywords、summary 或 subject')
    if resource_type == 'news' and field != 'all':
        raise ValueError('新闻仅验证全部字段检索')
    if resource_type == 'video' and field == 'author':
        raise ValueError('站方视频检索不提供作者字段')
    if resource_type == 'video' and field == 'subject':
        raise ValueError('视频主题词已测均为零，字段有效性未确认')
    delay = 1 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    p = {'q': keyword.strip(), 'pi': page - 1, 'ps': page_size, 't': types[resource_type], 'field': fields[field], 'lang': 'chinese', 'siteID': '14', 'sublibID': ''}
    r = requests.post(URL, data=p, timeout=20)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or type(d.get('total')) is not int or d['total'] < 0 or (not isinstance(d.get('hits'), list)):
        raise ValueError('未识别平台返回的检索结果')
    expected = min(page_size, max(0, d['total'] - (page - 1) * page_size))
    if len(d['hits']) != expected:
        raise ValueError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for h in d['hits']:
        if resource_type in ('figure', 'video', 'news') and h.get('type') != types[resource_type]:
            raise ValueError('题录类型与请求不符')
        x = h.get('source') or {}
        title = x.get('searchTitle')
        if not title:
            raise ValueError('题名缺失')
        content_id = str(x.get('ID') or '')
        if not content_id.isdigit():
            raise ValueError('内容编号缺失或格式不符')
        path = 'initDatabaseDetail' if resource_type == 'report' else 'bookDetail' if resource_type == 'book' else None
        args = {'siteId': '14', 'contentId': content_id, 'contentType': 'literature'} if resource_type == 'report' else {'SiteID': '14', 'ID': content_id}
        figure_url = 'https://www.pishu.com.cn/skwx_ps/multimedia/ImageDetail?' + urlencode({'SiteID': '14', 'type': 'ImageTable', 'ID': content_id, 'ContentType': 'MultimediaImageContentType', 'isHost': 'null'}) if resource_type == 'figure' else None
        item = {'id': content_id, 'search_hit_id': h.get('id'), 'url': 'https://www.pishu.com.cn/skwx_ps/' + path + '?' + urlencode(args) if path else figure_url, 'title': title, 'authors': x.get('authors'), 'book_title': x.get('bookTitle'), 'book_id': x.get('bookID'), 'isbn': x.get('ISBN'), 'series': x.get('bookDeriesName'), 'published': x.get('publishDate'), 'keywords': x.get('keyWords')}
        if resource_type == 'news':
            link = x.get('link')
            source_link = None
            if isinstance(link, str):
                try:
                    u = urlsplit(link)
                    if u.scheme == 'https' and u.hostname == 'www.pishu.com.cn' and (not u.username) and (not u.password) and (u.port in (None, 443)) and (not u.query) and (not u.fragment) and u.path.endswith('/' + content_id + '.shtml'):
                        source_link = link
                except ValueError:
                    pass
            item['source_link_unverified'] = source_link
        items.append(item)
    result = {'source': '社会科学文献出版社皮书数据库公开题录', 'source_url': 'https://www.pishu.com.cn/skwx_ps/search', 'keyword': keyword.strip(), 'resource_type': resource_type, 'total': d['total'], 'page': page, 'items': items, 'note': '按平台资源类型筛选的公开题录，不读取全文；不代表浙江大学身份、已购范围或全文权限。'}
    result['note'] += ' 已按源总数及请求页次校验条数；站方不回显页码，跨请求数据可能变化。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 站方可能分词匹配，未回显字段或页码，结果并非精确短语匹配的证明。'
    if resource_type == 'figure' and field == 'author':
        result['note'] += ' 站方提供图表作者字段，但已测关键词均为零，字段有效性未确认。'
    if resource_type == 'news':
        result['note'] += ' 新闻仅返回题录及通过格式校验的站方原链接，逐条可用性未保证；抽样曾有404及标题未确认，学校权限未知。'
    if resource_type in ('figure', 'video'):
        result['note'] += ' 图表和视频仅返回题录；图表详情链接按站方公开路径构造，统计数值、播放及机构权限未验证；视频详情链接未验证。'
    return result
