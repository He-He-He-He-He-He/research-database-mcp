"""广东省政府门户站内政策法规标签搜索。"""
import release_runtime
import urllib.parse
import requests

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 的整数')
    with requests.Session() as session:
        homepage = session.get('https://search.gd.gov.cn/', timeout=20)
        homepage.raise_for_status()
        token = session.cookies.get('XSRF-TOKEN')
        if not token:
            raise RuntimeError('官方页面未提供会话令牌')
        params = {'label': '政策法规', 'keywords': keyword.strip(), 'sort': 'smart', 'site_id': '2', 'range': 'site', 'position': 'title', 'page': page, 'tag_name': '政策法规', 'recommand': 1, 'gdbsDivision': '440000', 'service_area': 1}
        response = session.post('https://search.gd.gov.cn/api/search/all', json=params, headers={'X-XSRF-TOKEN': urllib.parse.unquote(token)}, timeout=60)
        response.raise_for_status()
        data = response.json()
    if data.get('errcode') != 0 or not isinstance(data.get('data', {}).get('news', {}).get('list'), list):
        raise RuntimeError('官方检索响应错误或结构异常')
    news = data['data']['news']
    if news.get('total') == 0 and (not news['list']):
        raise RuntimeError('官方搜索返回空结果；服务曾出现异常清零，无法确认是否真正无匹配，请稍后复查原站')
    if not isinstance(news.get('total'), int) or news['total'] < 0:
        raise RuntimeError('官方搜索返回的总数无效')
    if len(news['list']) > news['total'] or (not news['list'] and (page - 1) * 20 < news['total']):
        raise RuntimeError('官方搜索总数与页内条目不一致，请稍后复查原站')
    return {'source': '广东省政府门户站内搜索：政策法规标签', 'keyword': keyword.strip(), 'page': page, 'total': news.get('total'), 'items': news['list'], 'notice': '按标题检索本站政策法规标签；包含国家及地方文件，摘要非全文，标签与状态字段不足以判定当前效力。'}
