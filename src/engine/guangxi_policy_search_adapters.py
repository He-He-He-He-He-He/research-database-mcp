"""广西政府政策文件库官方站点调用的搜索接口。"""
import release_runtime
import requests
ENDPOINT = 'https://api.so-gov.cn/query/s'
TAB = 'e51112c1222af9b93b377335e19ceaf9'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000 的整数')
    r = requests.post(ENDPOINT, data={'siteCode': '4500000123_zck', 'pageSize': 10, 'page': page, 'qt': keyword.strip(), 'timeOption': 2, 'tab': TAB}, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('ok') is not True:
        raise RuntimeError('官方检索服务报错：' + str(d.get('msg')))
    config = d.get('data', {}).get('config', {})
    if config.get('id') != TAB or config.get('name') != '全部':
        raise RuntimeError('原站搜索分类发生变化')
    result = d['data'].get('result', {}).get('search', {})
    docs = result.get('docs')
    total = result.get('total')
    if not isinstance(docs, list) or not isinstance(total, int) or total < 0:
        raise RuntimeError('原站返回结构异常')
    if not docs and (page - 1) * 10 < total or len(docs) > total:
        raise RuntimeError('原站结果数量不一致')
    return {'source': '广西壮族自治区政府政策文件库', 'keyword': keyword.strip(), 'page': page, 'total': total, 'items': docs, 'notice': '标题或关键词搜索；结果含不同机关和可能的历史文件，URL 保留原站原值，正文、附件与现行效力须核对。'}
