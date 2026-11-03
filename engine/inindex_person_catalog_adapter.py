"""引得历代人物资料普通姓名检索单页题录。"""
import release_runtime
import requests
URL = 'https://api.cloud.xyinde.com/cbdb/v3/basicSearch/getBiogBasisInfoList'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('姓名关键词须为1–100字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页码须为1–10000')
    p = {'keyword': keyword.strip(), 'page': str(page), 'pageSize': '20', 'sort': 'notNullColumnCount,desc;indexYear,desc', 'officeIdList': '', 'addrIdList': '', 'startYear': '', 'endYear': ''}
    r = requests.post(URL, data=p, timeout=30)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('引得未返回 JSON') from None
    pg = j.get('npage') if isinstance(j, dict) else None
    if j.get('success') is not True or not isinstance(pg, dict) or pg.get('page') != page or (pg.get('pageSize') != 20) or (not isinstance(pg.get('totalCount'), int)) or (not isinstance(j.get('list'), list)) or (len(j['list']) > 20):
        raise RuntimeError('人物检索响应或页码异常')
    fields = ('personid', 'biogNameChn', 'biogAltNameChn', 'dynastyChn', 'indexAddrNameChn', 'biogBirthyear', 'biogDeathyear', 'indexYear')
    items = []
    for x in j['list']:
        if not isinstance(x, dict) or not isinstance(x.get('personid'), str) or (not x.get('biogNameChn')):
            raise RuntimeError('人物编号或姓名缺失')
        items.append({k: x.get(k) for k in fields})
    return {'source': '引得中国历代人物传记资料库', 'query': keyword.strip(), 'field': '姓名及可能匹配别名', 'page': page, 'page_size': 20, 'total': pg['totalCount'], 'total_pages': pg.get('totalPage'), 'items': items, 'note': '原站普通人物检索单页；保留原始生卒及索引年份，包括0，0 的含义须核对原站。此次未确认浙大机构身份，不代表传记全文或全部馆藏权限。'}
