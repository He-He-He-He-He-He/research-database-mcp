"""爱教材校园 IP 全文检索结果页短片段，不访问正文或阅读链接。"""
import release_runtime
import json, re, requests
from bs4 import BeautifulSoup
URL = 'https://www.itextbook.cn/f/book/retrieveInfo'

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f`~!@#$%^&*_+=<>?"{}|/;\\\\\\[\\]·！￥%……&*（）()。——+={}|《》？“”【】‘]', keyword):
        raise ValueError('关键词须为 1–100 字且符合站方普通搜索规则')
    if type(page) is not int or not 1 <= page <= 1000 or type(limit) is not int or (not 1 <= limit <= 10):
        raise ValueError('page 或 limit 无效')
    q = keyword.strip()
    body = {'oneSearch': [{'fieldType': '80', 'relationshipType': 10, 'fieldVal': q, 'vague': 0}], 'pageNo': str(page), 'pageSize': '10'}
    try:
        r = requests.post(URL, data={'paramJson': json.dumps(body, ensure_ascii=False)}, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('全文检索服务不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        if not re.search('浙江大学\\s*IP\\s*(?:Reader|读者)', text, re.I):
            raise RuntimeError('未确认浙江大学 IP 读者')
        queries = p.select('input[name=plist]')
        pg = p.select_one('input[name=pageNo]')
        nav = p.select_one('div.page')
        if len(queries) != 1 or queries[0].get('fieldval') != q or queries[0].get('fieldtype') != '80' or (not pg) or (pg.get('value') != str(page)):
            raise RuntimeError('检索条件或页码未确认')
        match = re.search('(?:total\\s*:|总计[：:])\\s*([\\d,]+)', nav.get_text(' ', strip=True), re.I) if nav else None
        if not match:
            raise RuntimeError('站方总数未识别')
        total = int(match.group(1).replace(',', ''))
        cards = p.select('.book-item')
        expected = min(10, max(0, total - (page - 1) * 10))
        if len(cards) != expected:
            raise RuntimeError('结果数与当前页不一致')
        items = []
        for x in cards[:limit]:
            snippet = x.select_one('p.desc')
            source = x.select_one('p.proven')
            action = x.select_one('a[onclick^="authorityToJudge("]')
            if not snippet or not source:
                raise RuntimeError('片段或来源缺失')
            text_snippet = snippet.get_text(' ', strip=True)
            raw_source = source.get_text(' ', strip=True)
            if not text_snippet or not raw_source:
                raise RuntimeError('片段或来源为空')
            access = None
            if action:
                found = re.search("^authorityToJudge\\('[^']*','([^']*)'", action.get('onclick', ''))
                if found and re.fullmatch('[\\u3400-\\u9fffA-Za-z0-9 ]{1,30}', found.group(1)):
                    access = found.group(1)
            items.append({'snippet_raw': text_snippet, 'source_raw': raw_source, 'access_label_raw': access})
        return {'source': '爱教材全文搜索结果页', 'institution': '浙江大学 IP Reader', 'query': q, 'page': page, 'source_page_size': 10, 'total_raw': total, 'source_page_items': len(cards), 'page_truncated': len(items) < len(cards), 'items': items, 'note': '仅返回结果页显示的短片段及来源原文；片段可能截断，同书可出现多次，记录数不是图书数。站方访问标签按页面原值保留，不能推断逐书正文权限；不输出阅读或会话链接。'}
    except requests.RequestException:
        raise RuntimeError('爱教材连接失败') from None
