"""浙大馆藏零星电子刊名单，依据馆方公开说明页。"""
import release_runtime
from urllib.parse import urljoin
import requests
import re
from bs4 import BeautifulSoup
BASE = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1339'
CATEGORIES = ('人文', '社会科学（含法律）', '理学', '工学与信息学', '农业生命环境', '医学')

def zju_individual_journals(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    r = requests.get(BASE, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    tables = s.select('.richbox table')
    if len(tables) != len(CATEGORIES):
        raise ValueError('馆方分类或表格发生变化，需核对')
    out = []
    for category, table in zip(CATEGORIES, tables):
        for tr in table.select('tr'):
            cells = tr.find_all('td', recursive=False)
            if len(cells) < 5 or not cells[0].get_text(strip=True).isdigit():
                continue
            a = cells[2].find('a', href=True)
            name = cells[2].get_text(' ', strip=True)
            if keyword.casefold() not in ' '.join((x.get_text(' ', strip=True) for x in cells)).casefold():
                continue
            note = cells[5].get_text(' ', strip=True) if len(cells) > 5 else ''
            if re.search('账号|帐号|用户名|密码|口令|username|password|login', note, re.I):
                note = '认证信息请在馆方页面查看'
            out.append({'category': category, 'issn': cells[1].get_text(' ', strip=True), 'title': name, 'url': urljoin(BASE, a['href']) if a else None, 'publisher': cells[3].get_text(' ', strip=True), 'coverage_from': cells[4].get_text(' ', strip=True), 'note': note})
    return {'source': '浙大图书馆零星电子刊说明页', 'source_url': BASE, 'items': out, 'note': '馆方公布名单；各刊订购年限、认证及全文须逐项核验，不保存或获取账号。'}
