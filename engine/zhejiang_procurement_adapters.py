"""浙江政府采购网首页公开公告，只读。"""
import release_runtime
import argparse, json, sys
from urllib.parse import urlencode
from research import get

def zj_procurement_home(keyword=''):
    payload = get('https://zfcg.czt.zj.gov.cn/portal/searchHome', body={'code': '110-606633', 'pageSize': 5})
    if not payload.get('success') or not isinstance(payload.get('result'), dict):
        raise ValueError('上游没有返回成功结果')
    data = payload['result'].get('data') or {}
    rows = data.get('children')
    if not isinstance(rows, list):
        raise ValueError('上游公告结构变化')
    items = []
    for x in rows:
        if keyword not in (x.get('title') or ''):
            continue
        params = urlencode({'parentId': data.get('firstId', ''), 'articleId': x.get('articleId', '')})
        items.append({'title': x.get('title'), 'date': x.get('publishDateString'), 'region': x.get('districtName'), 'buyer': x.get('purchaseName'), 'method': x.get('purchaseMethod'), 'url': 'https://zfcg.czt.zj.gov.cn/site/detail?' + params, 'is_sticky': x.get('isStickLevel')})
    return {'source': '浙江政府采购网', 'source_url': 'https://zfcg.czt.zj.gov.cn/', 'scope': '仅官网首页政府采购公告的当前列表，关键词仅本地筛选该列表', 'items': items, 'note': '并非全站检索或历史分页；正文和附件请在官网查看。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword', nargs='?', default='')
    a = p.parse_args()
    print(json.dumps(zj_procurement_home(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
