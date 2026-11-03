"""浙大大型文献库的丛书详情，不读取原文或用户标签。"""
import release_runtime
import argparse, json, re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zju_doclib_api import BASE

def detail(book_id):
    if not isinstance(book_id, str) or not re.fullmatch('[a-fA-F0-9]{32}', book_id):
        raise ValueError('丛书 ID 须为 32 位十六进制')
    book_id = book_id.lower()
    url = BASE + 'book?' + urlencode({'id': book_id})
    with urlopen(url, timeout=20) as r:
        s = BeautifulSoup(r.read().decode('utf-8'), 'html.parser')
    tables = [x for x in s.select('table') if x.select_one('h2') and x.select_one('p.title')]
    if len(tables) != 1:
        raise RuntimeError('无法确认丛书详情')
    table = tables[0]
    title = table.select_one('h2').get_text(' ', strip=True)
    fields = []
    for tr in table.select('tr'):
        left = tr.select_one('p.title')
        right = tr.select_one('p.des')
        if left and right:
            label = left.get_text(' ', strip=True).rstrip('：:')
            if label != '常用标签':
                fields.append({'label': label, 'value': right.get_text(' ', strip=True)})
    if not title or not fields:
        raise RuntimeError('丛书题名或字段缺失')
    return {'source': '浙江大学大型文献信息库', 'title': title, 'fields': fields, 'record_url': url, 'note': '仅丛书级目录数据，馆方提示数据未完整；不代表所有子卷或全文可读。上游 HTTP 明文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('id')
    a = p.parse_args()
    print(json.dumps(detail(a.id), ensure_ascii=False, indent=2))
