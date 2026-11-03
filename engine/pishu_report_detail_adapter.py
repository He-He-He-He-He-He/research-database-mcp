"""皮书数据库报告公开基本题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup

def detail(report_id, include_abstract=False):
    if not isinstance(report_id, str) or not re.fullmatch('\\d{1,15}', report_id):
        raise ValueError('报告编号须为数字')
    if type(include_abstract) is not bool:
        raise ValueError('摘要开关须为布尔值')
    url = 'https://www.pishu.com.cn/skwx_ps/initDatabaseDetail'
    r = requests.get(url, params={'siteId': '14', 'contentId': report_id, 'contentType': 'literature'}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    suffix = '_皮书数据库'
    if not title.endswith(suffix) or not title[:-len(suffix)].strip():
        raise RuntimeError('未识别报告页面题名')
    lists = soup.select('ul.baogao-list1')
    if len(lists) != 1:
        raise RuntimeError('未识别唯一的报告基本信息')
    fields = []
    for li in lists[0].find_all('li', recursive=False):
        k, sep, v = li.get_text(' ', strip=True).partition('：')
        if sep and k in ('报告作者', '所属图书', '图书作者', '出版时间'):
            fields.append({'label': k, 'value': v.strip()})
    if not any((x['label'] == '所属图书' and x['value'] for x in fields)):
        raise RuntimeError('未识别报告所属图书')
    out = {'source': '皮书数据库公开报告书目', 'id': report_id, 'title': title[:-len(suffix)].strip(), 'record_url': r.url, 'fields': fields, 'note': '仅报告可见的基本书目，不含正文；不证明学校已购或全文权限。'}
    if include_abstract:
        summaries = soup.select('.ztk-main .summaryCon_more') or soup.select('.ztk-main .summaryCon_m')
        if len(summaries) > 1:
            raise RuntimeError('报告摘要区不唯一')
        out['abstract'] = summaries[0].get_text(' ', strip=True) if summaries else None
        out['keywords'] = [a.get_text(' ', strip=True) for a in soup.select('.ztk-main .d-keyword a') if a.get_text(' ', strip=True)]
        out['note'] = '站方可见摘要与关键词（可能缺失），不含正文；不证明学校已购或全文权限。'
    return out
