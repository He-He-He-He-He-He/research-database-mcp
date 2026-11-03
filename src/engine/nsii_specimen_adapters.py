"""国家标本资源共享平台：按学名或中文名查询单页题录。"""
import release_runtime
import argparse, json, re, sys
from urllib.parse import urlencode, quote
from research import fetch
ENDPOINT = 'https://site.nsii.org.cn/API/NSIISpecimenAgent2.ashx'

def search(name, page=1, mode='scientific'):
    if not isinstance(name, str) or not name.strip() or len(name) > 100 or re.search('["\\\\\\r\\n]', name):
        raise ValueError('名称不能为空，且不能包含引号、反斜线或换行')
    if not 1 <= page <= 100 or mode not in ('scientific', 'chinese'):
        raise ValueError('页码须为1到100，mode须为 scientific 或 chinese')
    field = 'sname' if mode == 'scientific' else 'commonName'
    q = field + ':"' + name.strip() + '"'
    url = ENDPOINT + '?' + urlencode({'q': q, 'wt': 'json', 'start': (page - 1) * 10})
    raw = fetch(url).strip()
    match = re.fullmatch('processSpecimenResults\\((\\{.*\\})\\s*\\)\\s*;?', raw, re.S)
    if not match:
        raise ValueError('上游返回格式变化或需要认证')
    payload = json.loads(match.group(1))
    r = payload.get('response')
    if not isinstance(r, dict) or not isinstance(r.get('docs'), list):
        raise ValueError('未取得标本检索结果')
    items = []
    for x in r['docs']:
        uuid = str(x.get('uuid', ''))
        if not re.fullmatch('[a-fA-F0-9-]{1,80}', uuid):
            uuid = ''
        items.append({'scientific_name': x.get('sname'), 'chinese_name': x.get('commonName'), 'collector': x.get('recordedBy'), 'locality': x.get('lessgeo'), 'provider_code': x.get('provider'), 'institution_id': x.get('datasetid'), 'detail_url': 'https://www.nsii.org.cn/2017/specimen.php?id=' + quote(uuid) if uuid else None})
    return {'source': 'https://www.nsii.org.cn/2017/query.php', 'terms': 'https://www.nsii.org.cn/2017/doc.php?n=dataagreement', 'query': name, 'mode': mode, 'page': page, 'total': r.get('numFound'), 'items': items, 'scope': '单次单页标本题录，不自动批量下载'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('name')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--mode', choices=['scientific', 'chinese'], default='scientific')
    a = p.parse_args()
    print(json.dumps(search(a.name, a.page, a.mode), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
