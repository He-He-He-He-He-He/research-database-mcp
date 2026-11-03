"""浙江省行政规范性文件库 sourceType 1 和 3 的官网 HTML 正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://zjsftbascweb.zjsft.gov.cn/data/zjdatabase/census/fLibrary/getFileHtml'

def zhejiang_normative_html(document_id, source_type, timeout=25):
    if not isinstance(document_id, str) or not re.fullmatch('[A-Za-z0-9-]{1,80}', document_id):
        raise ValueError('文档 ID 无效')
    if isinstance(source_type, bool) or source_type not in (1, 3):
        raise ValueError('仅支持已验证的 sourceType 1 或 3')
    r = requests.get(URL, params={'sourceType': source_type, 'id': document_id}, timeout=timeout, allow_redirects=False)
    r.raise_for_status()
    if r.status_code != 200:
        raise ValueError('正文发生重定向或状态异常')
    result = r.json().get('result', {})
    data = result.get('data')
    if result.get('code') != 4000 or not isinstance(data, dict) or data.get('code') != 0 or (not isinstance(data.get('msg'), str)):
        raise ValueError('站方未返回可用正文')
    soup = BeautifulSoup(data['msg'], 'html.parser')
    for x in soup.select('script,style'):
        x.decompose()
    for x in soup.select('br'):
        x.replace_with('\n')
    for x in soup.select('p,div,tr'):
        x.insert_before('\n')
        x.insert_after('\n')
    body = soup.body if soup.body else soup
    text = '\n'.join((line.strip() for line in body.get_text().splitlines() if line.strip()))
    if not text:
        raise ValueError('正文为空')
    return {'source': '浙江省司法厅行政规范性文件库 HTML 正文', 'source_url': r.url, 'id': document_id, 'source_type': source_type, 'release_department': data.get('releaseDeptName'), 'text': text, 'note': '状态需通过目录查询及其他官方资料核对；正文文字化不保留表格、图片或附件格式，也不保证全文无附件。此入口未覆盖 sourceType 0、2、4。'}
