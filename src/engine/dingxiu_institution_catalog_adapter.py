"""鼎秀古籍校园 IP 直接书目检索，仅输出题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.ding-xiu.com/ancientbook/portal/document/'

def _plain(s):
    return BeautifulSoup(s, 'html.parser').get_text('', strip=True) if isinstance(s, str) else s

def search(keyword, page=1, limit=5, field='all', dynasty_code='', author=''):
    if not isinstance(author, str) or len(author) > 100 or re.search('["\\\\\\x00-\\x1f]', author):
        raise ValueError('作者须为不含引号、反斜杠及控制字符的单行文本')
    author = author.strip()
    if author and (field != 'bookname' or dynasty_code):
        raise ValueError('作者组合仅验证书名字段，暂不叠加朝代')
    if not isinstance(dynasty_code, str) or (dynasty_code and (not re.fullmatch('[0-9]{1,3}', dynasty_code))):
        raise ValueError('朝代代码无效')
    if field not in ('all', 'bookname', 'author', 'version', 'chapter', 'chapterant'):
        raise ValueError('不支持的检索字段')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('["\\\\\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为1–100字且不含引号、反斜杠及控制字符')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页最多10条')
    q = keyword.strip()
    expr = f'(bookname:"{q}" OR author:"{q}" OR version:"{q}" OR chapter:"{q}")' if field == 'all' else f'{field}:"{q}"'
    if author:
        expr = '(' + expr + ' AND author:"' + author + '")'
    with requests.Session() as s:
        r = s.get(BASE + 'index.do', timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        i = p.select_one('#nologin')
        if not i or not re.search('机构\\s*[:：]\\s*浙江大学', i.get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构身份')
        dynasty_name = ''
        if dynasty_code:
            options = [o for o in p.select('select[name=dynastylist] option') if o.get('value') == dynasty_code]
            if len(options) != 1:
                raise ValueError('朝代代码不在站方列表中')
            dynasty_name = options[0].get_text(' ', strip=True)
            if not dynasty_name:
                raise RuntimeError('站方朝代名称缺失')
            expr = '(' + expr + ' AND dynasty:"' + dynasty_code + '")'
        body = {'searchType': 'tablelist', 'searchWord': q, 'searchWhere': expr, 'catagoryCode': '', 'startPage': str(page), 'pageSize': str(limit), 'order': ''}
        r = s.post(BASE + 'documentPageList.do', data=body, timeout=25)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('鼎秀未返回 JSON') from None
    d = j.get('resultPage') if isinstance(j, dict) and j.get('operateFlag') is True else None
    if not isinstance(d, dict) or d.get('startPage') != page or d.get('pageSize') != limit or (type(d.get('recordCount')) is not int) or (d['recordCount'] < 0) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('书目分页响应异常')
    expected = min(limit, max(0, d['recordCount'] - (page - 1) * limit))
    if len(d['list']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or type(x.get('bookid')) is not int or (not isinstance(x.get('sim_bookname'), str)):
            raise RuntimeError('书目编号或题名缺失')
        if dynasty_code and str(x.get('dynasty')) != dynasty_code:
            raise RuntimeError('结果朝代与所选条件不符')
        item = {'book_id': x['bookid'], 'guid': x.get('bookguid'), 'title': _plain(x['sim_bookname']), 'title_traditional': _plain(x.get('tra_bookname')), 'author': _plain(x.get('sim_author')), 'edition': _plain(x.get('sim_version')), 'volume': _plain(x.get('sim_volumename')), 'dynasty': x.get('sim_dynastyname')}
        omitted = []
        for key in ('sim_bookname', 'tra_bookname', 'sim_author', 'sim_version', 'sim_volumename'):
            v = x.get(key)
            if v is not None and (not isinstance(v, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I)):
                item['source_' + key + '_raw'] = None
                omitted.append(key)
            else:
                item['source_' + key + '_raw'] = v
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': '鼎秀古籍全文检索平台', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'source_total': d['recordCount'], 'items': items[:limit], 'note': '普通检索包括书名、作者、版本和篇章，不等于题名精确匹配；仅返回题录，逐书正文或影像权限未验证。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '按站方高级检索字段请求；站方未回显筛选字段，结果可能受繁简及分词影响；仅返回题录，正文、注文关键词不代表完整正文或逐书影像权限。'
    result['note'] += ' source_*_raw 保留安全站方原值及高亮，含链接、疑似凭据或异常结构时省略并标记；按总数及回显页码校验条数，数据可能变化。'
    if dynasty_code:
        result['dynasty_filter'] = {'code': dynasty_code, 'name': dynasty_name}
        result['note'] += ' 站方未回显完整筛选条件，已核对返回记录朝代代码。'
    if author:
        result['author_requested'] = author
        result['note'] += ' 书名与作者 AND 组合已抽验，站方不回显条件，匹配须核对。'
    return result
