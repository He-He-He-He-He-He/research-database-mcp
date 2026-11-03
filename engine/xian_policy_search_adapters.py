"""西安市政府政策文件库：西安市文件分类检索。"""
import release_runtime
import requests
ENDPOINT = 'https://api.so-gov.cn/query/s'
TAB = 'f8f55e9f9a0a95b4da5c7ec2e04eae1f'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 整数')
    params = {'tab': TAB, 'siteCode': '6101000007_zck', 'qt': keyword.strip(), 'searchFlag': 1, 'sitePath': 'true', 'pageSize': 20, 'page': page, 'styleForm': 0, 'keyPlace': '', 'sort': ''}
    r = requests.post(ENDPOINT, data=params, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('ok') is not True:
        raise RuntimeError('搜索服务错误：' + str(d.get('msg')))
    data = d.get('data', {})
    config = data.get('config', {})
    if config.get('id') != TAB or config.get('name') != '西安市文件':
        raise RuntimeError('搜索分类发生变化')
    result = data.get('result', {}).get('search', {})
    docs = result.get('docs')
    total = result.get('total')
    if not isinstance(docs, list) or not isinstance(total, int) or total < 0:
        raise RuntimeError('搜索响应结构异常')
    if not docs and (page - 1) * 20 < total or len(docs) > total:
        raise RuntimeError('搜索总数与结果不一致')
    return {'source': '西安市政策文件库西安市文件分类', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': docs, 'notice': '结果含市区部门转载上级文件、公告及失效文件；标题、摘要和状态需结合原文及后续修改核查。'}
