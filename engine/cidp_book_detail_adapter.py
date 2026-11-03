"""CIDP 电子图书公开书目信息；不读取或下载电子书。"""
import release_runtime
import argparse, json, re, subprocess
from bs4 import BeautifulSoup
from cidp_search_adapters import BASE

def detail(book_id):
    if not isinstance(book_id, str) or not re.fullmatch('[a-fA-F0-9]{32}', book_id):
        raise ValueError('电子书编号需为32位十六进制')
    url = BASE + '/web/Ebook/' + book_id
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('CIDP 书目请求失败')
    s = BeautifulSoup(p.stdout.decode('utf-8', 'replace'), 'html.parser')
    box = s.select_one('.dzs-box1')
    title = box.select_one('.dzs-bt').get_text(' ', strip=True) if box and box.select_one('.dzs-bt') else None
    table = box.select_one('table.dzs-wenzi') if box else None
    if not title or not table:
        raise RuntimeError('未识别电子书详情，页面可能变更或需登录')
    fields = []
    for cell in table.select('td'):
        text = ' '.join(cell.get_text(' ', strip=True).split())
        m = re.match('^(作者|出版日期|纸质图书定价|书号|文件大小|字数|页数)\\s*[:：]\\s*(.*)$', text)
        if m:
            fields.append({'label': m.group(1), 'value': m.group(2)})
    if not any((x['label'] == '作者' for x in fields)) or not any((x['label'] == '书号' for x in fields)):
        raise RuntimeError('详情关键书目字段缺失')
    return {'source': 'CIDP制造业数字资源平台', 'title': title, 'fields': fields, 'record_url': url, 'note': '仅公开电子书书目；搜索列表日期是加入时间，详情出版日期为出版信息，口径不同。正文须按页面许可访问；不表示浙大已购或可下载。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('id')
    a = p.parse_args()
    print(json.dumps(detail(a.id), ensure_ascii=False, indent=2))
