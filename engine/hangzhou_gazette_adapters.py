"""杭州市人民政府公报公开政策文件检索。"""
import release_runtime
import json, subprocess
from urllib.parse import urljoin, urlparse
BASE = 'https://zfgb.hangzhou.gov.cn/'
API = BASE + 'api/content_center/document/search_bulletin'
FIELDS = ('id', 'title', 'PubDate', 'column_name', 'fileNum', 'year', 'year_num', 'total_num', 'publisher', 'valid')

def search(keyword='', page=1, page_size=15, content='', publisher='', number='', start_date='', end_date=''):
    if not 1 <= int(page) <= 10000 or not 1 <= int(page_size) <= 50:
        raise ValueError('页码必须为正，每页条数须为 1–50')
    d = {'keyword': keyword, 'keyword_content': content, 'publisher': publisher, 'tag_type': [], 'column_id': '', 'file_type': '', 'file_num': number, 'start_date': start_date, 'end_date': end_date, 'year': '', 'year_num': '', 'total_num': '', 'subject_class': [], 'sort_order': 1, 'page_size': int(page_size), 'page_index': int(page)}
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', '-H', 'Content-Type: application/json;charset=UTF-8', '--data-binary', json.dumps(d, ensure_ascii=False), API], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('杭州市公报查询失败: ' + p.stderr.strip())
    try:
        result = json.loads(p.stdout)
        if result.get('code') != 200 or not isinstance(result.get('data'), dict):
            raise ValueError('响应状态异常')
        data = result['data']
        rows = data['list']
        total = int(data['total'])
        if not isinstance(rows, list) or int(data['page_index']) != int(page):
            raise ValueError('页码或结果结构异常')
        items = []
        for row in rows:
            if not isinstance(row, dict) or not row.get('title') or (not row.get('pub_url')):
                raise ValueError('结果缺少标题或链接')
            target = urljoin(BASE, row['pub_url'])
            parsed = urlparse(target)
            if parsed.scheme != 'https' or parsed.hostname != 'zfgb.hangzhou.gov.cn':
                raise ValueError('结果链接不是公报官网 HTTPS 页面')
            item = {k: row[k] for k in FIELDS if k in row}
            item['url'] = target
            items.append(item)
    except (ValueError, TypeError, KeyError) as e:
        raise RuntimeError('杭州市公报响应异常，未返回局部结果') from e
    return {'source': '杭州市人民政府公报网站', 'keyword': keyword, 'page': int(page), 'page_size': int(page_size), 'total': total, 'items': items, 'scope': '公报收录的文件元数据；官网状态字段不是法律效力的独立核验，使用时需查阅官方原文及现行文件'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=15)
    p.add_argument('--content', default='')
    p.add_argument('--publisher', default='')
    p.add_argument('--number', default='')
    p.add_argument('--start-date', default='')
    p.add_argument('--end-date', default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.page_size, a.content, a.publisher, a.number, a.start_date, a.end_date), ensure_ascii=False, indent=2))
