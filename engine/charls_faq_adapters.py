"""北京大学 CHARLS 常见问题公开文本。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://charls.pku.edu.cn/Faq/cjwt.htm'

def charls_faq(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词长度不超过 100 字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    area = s.select_one('#vsb_content ol')
    if not area:
        raise ValueError('未识别常见问题')
    out = []
    for li in area.find_all('li', recursive=False):
        strong = li.find('strong')
        text = li.get_text('\n', strip=True)
        if strong and keyword in text:
            out.append({'question': strong.get_text(' ', strip=True), 'text': text})
    if not out and (not keyword):
        raise ValueError('未识别常见问题条目')
    return {'url': URL, 'items': out, 'note': '公开问答，不提供微观数据；访问和申请条件以项目当前说明为准。'}
