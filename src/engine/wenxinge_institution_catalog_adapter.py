"""Wenxinge institution search catalog, excluding retrieved text snippets."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.wenxin-ge.com/wenxinge/'
FIELDS = ('sim_bookname', 'tra_bookname', 'sim_author', 'tra_author', 'sim_dynastyname', 'tra_dynastyname', 'sim_version', 'tra_version', 'sim_chapter', 'tra_chapter', 'sim_chapterant', 'tra_chapterant')

def search(keyword, page=1, limit=5, session=None, include_snippets=False, field='all', dynasty_code='', author=''):
    if not isinstance(author, str) or len(author) > 100 or re.search('["\\\\\\x00-\\x1f]', author):
        raise ValueError('作者须为不含引号、反斜杠和控制字符的单行文本')
    author = author.strip()
    if author and (field != 'bookname' or dynasty_code):
        raise ValueError('作者组合仅验证书名字段，暂不叠加朝代')
    if not isinstance(dynasty_code, str) or (dynasty_code and (not re.fullmatch('[0-9]{1,3}', dynasty_code))):
        raise ValueError('朝代代码无效')
    if field not in ('all', 'bookname', 'author', 'version', 'chapter', 'chapterant'):
        raise ValueError('不支持的检索字段')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('["\\\\\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字且不含引号、反斜杠或控制字符')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 12):
        raise ValueError('每页最多 12 条')
    if type(include_snippets) is not bool:
        raise ValueError('片段开关须为布尔值')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE + 'home/doc/index.do', timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if '浙江大学' not in p.get_text(' ', strip=True):
        raise RuntimeError('未确认浙江大学机构身份')

    def value(k):
        x = p.select_one('#' + k)
        if x is None:
            raise RuntimeError('缺少原站检索参数')
        return x.get('value', '')
    selected = FIELDS if field == 'all' else ('sim_' + field, 'tra_' + field)
    category = value('rootCatagoryCode')
    where = ' (' + ' OR '.join((f'{name}:"{q}"' for name in selected)) + ')'
    if author:
        where = '(' + where.strip() + ' AND (sim_author:"' + author + '" OR tra_author:"' + author + '"))'
    dynasty_name = ''
    if dynasty_code:
        options = [o for o in p.select('select[name=dynastylist] option') if o.get('value') == dynasty_code]
        if len(options) != 1:
            raise ValueError('朝代代码不在站方列表中')
        dynasty_name = options[0].get_text(' ', strip=True)
        if not dynasty_name:
            raise RuntimeError('站方朝代名称缺失')
        where = '(' + where.strip() + ' AND dynasty:"' + dynasty_code + '")'
    if category:
        where = 'categorys:' + category + '* AND ' + where
    body = {'searchType': 'tablelist', 'searchWord': q, 'ytzFlag': value('ytzFlag'), 'mhjsFlag': value('mhjsFlag'), 'catagoryCode': category, 'searchWhere': where, 'startPage': str(page), 'pageSize': str(limit), 'order': ''}
    r = s.post(BASE + 'home/document/documentPageList.do', data=body, timeout=35)
    r.raise_for_status()
    j = r.json()
    d = j.get('resultPage') if isinstance(j, dict) else None
    meta = j.get('resultMap') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('operateFlag') is not True or (not isinstance(d, dict)) or (not isinstance(meta, dict)) or (d.get('startPage') != page) or (d.get('pageSize') != limit) or (type(d.get('recordCount')) is not int) or (d['recordCount'] < 0) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('书目响应异常')
    expected = min(limit, max(0, d['recordCount'] - (page - 1) * limit))
    if len(d['list']) != expected:
        raise RuntimeError('站方返回书目条数与书数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('tra_bookname'), str)):
            raise RuntimeError('书目编号或名称缺失')
        if dynasty_code:
            codes = x.get('dynasty')
            codes = codes if isinstance(codes, list) else [codes]
            if dynasty_code not in [str(code) for code in codes]:
                raise RuntimeError('结果朝代与所选条件不符')
        item = {'id': x['id'], 'book_id': x.get('bookguid'), 'title': x['tra_bookname'], 'author': x.get('tra_author'), 'edition': x.get('tra_version'), 'dynasty_code': x.get('dynasty'), 'volume': x.get('tra_volumename'), 'permission_marker': x.get('dbQHashAuth')}
        if include_snippets and x.get('dbQHashAuth') is True:
            item['source_snippets'] = {}
            omitted = []
            for k in ('sim_chapter', 'tra_chapter', 'sim_chapterant', 'tra_chapterant'):
                v = x.get(k)
                if v is not None and (not isinstance(v, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I)):
                    item['source_snippets'][k] = None
                    omitted.append(k)
                else:
                    item['source_snippets'][k] = v
            if omitted:
                item['source_snippets_omitted'] = omitted
        items.append(item)
    result = {'source': '文心阁古籍数据库', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'book_count': d['recordCount'], 'chapter_hit_count': meta.get('chapterCount'), 'items': items[:limit], 'note': '普通搜索覆盖书名、作者、朝代、版本及正文和注文，命中书数与站方 chapterCount 命中笔数不同；按原始权限标记仅为 true 的条目返回站方搜索片段，不代表完整正文或逐书全文权限。' if include_snippets else '普通搜索覆盖书名、作者、朝代、版本及正文和注文，命中书数与站方 chapterCount 命中笔数不同；只输出书目，权限标记保留原站值，不代表全文可读。'}
    if include_snippets:
        result['note'] += ' 搜索片段含链接、疑似凭据标记或非文本结构时，相关字段省略并标记。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '按站方高级检索字段请求，命中书数与 chapterCount 命中笔数不同，站方未回显检索字段，结果可能受繁简及分词影响；只输出书目' + ('和有权限标记的原站搜索片段' if include_snippets else '') + '，不代表完整正文或逐书全文权限。'
    if include_snippets and field != 'all':
        result['note'] += ' 搜索片段含链接、疑似凭据标记或非文本结构时，相关字段省略并标记。'
    if dynasty_code:
        result['dynasty_filter'] = {'code': dynasty_code, 'name': dynasty_name}
        result['note'] += ' 站方未回显完整筛选条件，已核对返回记录朝代字段。'
    if author:
        result['author_requested'] = author
        result['note'] += ' 书名与作者 AND 组合已抽验，站方未回显条件，逐项匹配须核对。'
    return result
