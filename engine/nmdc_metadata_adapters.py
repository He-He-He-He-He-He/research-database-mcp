"""国家微生物科学数据中心公开资源元数据检索。"""
import release_runtime
import argparse, json, re, sys
from urllib.parse import urlencode
from research import get
BASE = 'https://nmdc.cn'
API = BASE + '/api/services/nmdcweb/api/dataset/metadata/page'

def search(keyword, page=1, size=5):
    if not keyword.strip() or len(keyword) > 150 or (not 1 <= page <= 10000) or (not 1 <= size <= 10):
        raise ValueError('关键词不能为空，页码须大于零，单页为1至10条')
    x = get(API, {'keyword': keyword, 'pageNum': page, 'pageSize': size, 'sortType': '', 'sortOrder': ''})
    d = x.get('data') if isinstance(x, dict) else None
    if x.get('status') != 0 or not isinstance(d, dict) or (not isinstance(d.get('content'), list)):
        raise ValueError('上游返回错误或结构变化')
    items = []
    for row in d['content']:
        ident = str(row.get('id') or '')
        safe = bool(re.fullmatch('[a-fA-F0-9]{24,32}', ident))
        items.append({'id': ident, 'title': row.get('chineseName'), 'english_title': row.get('englishName'), 'subject': row.get('subject'), 'resource_type': row.get('type'), 'keywords': row.get('keyword'), 'organization': row.get('organization'), 'published': row.get('releaseTime'), 'doi': row.get('doi'), 'cstr': row.get('cstr'), 'access_policy': row.get('accessRestrictions'), 'license': row.get('license'), 'detail_url': BASE + '/metadata/detail?' + urlencode({'id': ident}) if safe else None})
    return {'source': BASE + '/metadata', 'keyword': keyword, 'page': page, 'size': size, 'total': d.get('totalElements'), 'items': items, 'scope': '元数据目录；资源可能含软件、数据集等，访问和使用权限以各项说明为准'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.size), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
