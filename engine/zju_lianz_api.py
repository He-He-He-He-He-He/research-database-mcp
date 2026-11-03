"""浙江大学廉政文献专题库的题名跨库检索。"""
import release_runtime
import argparse, html, json, re
from urllib.request import Request, urlopen
from zju_lianz_subcollection_adapter import validate_page_data, annotate_opac_url
BASE = 'http://lianz.zju.edu.cn/'
CODES = 'CULTURALHISTORY,WONDERFULVIDEO,LAW,CLEANGOVERNMENTPIC,GREATSTATE,BOOKREVIEW,THEORETICALLITERATU,CLEANGOVERNANCEBOOK'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('关键词不能为空')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    with urlopen(Request(BASE + 'index/getDBConfigList', data=b'classcode=003'), timeout=20) as r:
        config = json.load(r)['data']
    dbs = [{'id': x['dbid'], 'code': x['dbcode'], 'name': x['cnname']} for x in config if x.get('defaultselected') == '1']
    if not dbs:
        raise RuntimeError('服务未返回默认检索子库')
    body = {'classcode': '003', 'selectField': 'sys_fld_sysid,题名,密级,分类,关键词,语言,作者单位,发表时间', 'searchConditions': [{'isAnd': 'and', 'field': '题名', 'fieldView': '题名', 'value': keyword, 'vague': '%'}], 'dbList': dbs, 'databasecode': CODES, 'limit': '20', 'treekey': '所属单位', 'treeSearchConditions': [], 'hospitalNames': '', 'pageNumber': page, 'saveLog': True, 'orderby': '题名', 'sort': 'desc'}
    req = Request(BASE + 'DigitalResources/getMultiSearchList', data=json.dumps(body, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json;charset=UTF-8'})
    with urlopen(req, timeout=25) as r:
        result = json.load(r)
    validate_page_data(result, page)
    items = []
    for x in result['data']:
        title = html.unescape(re.sub('<[^>]*>', '', x.get('题名', '')))
        items.append(annotate_opac_url({'title': title, 'source': x.get('databasename'), 'date': x.get('发表时间'), 'url': x.get('jumpUrl')}))
    return {'source': '浙江大学廉政文献专题库', 'query': keyword, 'field': '题名', 'page': page, 'total': result['countNumber'], 'items': items, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；结果跨多个子库，全文权限未验证。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
