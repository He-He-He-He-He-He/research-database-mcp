"""浙大图书馆 OPAC 按记录 ID 查询单条书目。"""
import release_runtime
import argparse, json, re, subprocess
from bs4 import BeautifulSoup
from zju_opac_api import URL

def detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('ZJU(?:01|09)\\d{9}', record_id):
        raise ValueError('请输入检索结果中的 ZJU01/ZJU09 加九位系统号')
    base = record_id[:5]
    number = record_id[5:]
    cmd = ['/usr/bin/curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', '--get', '--data-urlencode', 'func=find-b', '--data-urlencode', 'find_code=SYS', '--data-urlencode', 'request=' + number, '--data-urlencode', 'local_base=' + base, URL]
    proc = release_runtime.run(cmd, capture_output=True, timeout=30)
    if proc.returncode:
        raise RuntimeError('浙大书目服务访问失败')
    soup = BeautifulSoup(proc.stdout.decode('utf-8', 'replace'), 'html.parser')
    table = soup.select_one('#content_item_list_table')
    if not table:
        raise RuntimeError('未识别书目详情，可能无该记录或服务变化')
    fields = []
    last_label = None
    for row in table.find_all('tr'):
        label = row.select_one('td#bold')
        value = label.find_next_sibling('td') if label else None
        if label and value:
            k = ' '.join(label.get_text(' ', strip=True).split())
            v = ' '.join(value.get_text(' ', strip=True).split())
            if k:
                last_label = k
            k = k or last_label
            if k and v and (k not in ('摘要', '目录', '作者简介', '网络摘要')):
                fields.append({'label': k, 'value': v})
    if not any((f['label'].startswith('系统号') and f['value'] == number for f in fields)) or not any((f['label'] == '题名' for f in fields)):
        raise RuntimeError('详情系统号或题名无法匹配')
    return {'source': '浙江大学图书馆 OPAC', 'database': base, 'id': record_id, 'fields': fields, 'note': '书目记录及页面所示馆藏元数据，非电子全文；借出状态和可预约状态可能变化，请以原站为准。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('id')
    a = p.parse_args()
    print(json.dumps(detail(a.id), ensure_ascii=False, indent=2))
