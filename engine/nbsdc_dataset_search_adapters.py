"""国家基础学科公共科学数据中心数据集元数据查询。"""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
BASE = 'https://www.nbsdc.cn'
API = BASE + '/api/general/searchDataSet'

def search(keyword, page=1, size=5):
    if not keyword.strip() or len(keyword) > 150 or (not 1 <= page <= 10000) or (not 1 <= size <= 10):
        raise ValueError('关键词不能为空，页码须大于零，单页为1至10条')
    key = ''.join(keyword.split())
    body = {'pageNum': page, 'pageSize': size, 'sortCode': '', 'searchTerms': key, 'searchName': key, 'dataTypeId': 1, 'subject': '', 'baseFlag': '', 'sharingModel': '', 'isHighQuality': '', 'publishTime': '', 'dataOtherTypeId': -1}
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-filesize', '5242880', '-H', 'Content-Type: application/json', '--data-binary', json.dumps(body, ensure_ascii=False), API], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if len(r.stdout) > 5242880:
        raise ValueError('响应超过大小限制')
    d = json.loads(r.stdout)
    if not isinstance(d, dict) or not isinstance(d.get('list'), list):
        raise ValueError('上游响应格式变化')
    items = []
    for row in d['list']:
        ident = str(row.get('id') or '')
        safe = bool(re.fullmatch('[a-fA-F0-9]{24}', ident))
        items.append({'id': ident, 'title': row.get('name'), 'cstr': row.get('cstr'), 'doi': row.get('doi'), 'subjects': row.get('subjectName'), 'keywords': row.get('keyword'), 'published': row.get('publishTime'), 'publisher': row.get('publisherName'), 'access_policy': row.get('accessPolicy'), 'detail_url': BASE + '/general/dataDetail?' + urlencode({'id': ident, 'type': 1}) if safe else None})
    return {'source': BASE + '/general/dataSetHome', 'keyword': keyword, 'page': page, 'size': size, 'total': d.get('totalCount'), 'total_pages': d.get('totalPages'), 'items': items, 'scope': '科学数据集元数据；实际数据访问条件以官方详情和授权为准'}

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
