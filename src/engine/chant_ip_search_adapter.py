"""漢達文庫校园 IP 快速检索：仅读取少量书目位置。"""
import release_runtime
import re
from urllib.parse import quote, urlsplit, unquote, parse_qs, urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.chant.org'

def parse_result(html,keyword,source_url,limit=5,offset=0):
    from diagnostics import SourceError
    soup=BeautifulSoup(html,'html.parser');text=soup.get_text(' ',strip=True)
    if '[Zhejiang University]' not in text:
        raise SourceError('institution_identity_unconfirmed','结果页未识别浙大机构会话',url=source_url)
    u=urlsplit(source_url);target=parse_qs(u.query).get('Target')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    headings=[h.get_text(' ',strip=True) for h in soup.select('h1,h2,h3') if re.fullmatch(r'【.*】',h.get_text(' ',strip=True))]
    if u.scheme!='https' or u.hostname!='www.chant.org' or unquote(u.path)!='/result/FastSearch/'+keyword or (target is not None and target!=[keyword]) or (title!='漢達文庫 - 檢索結果 - '+keyword and '【'+keyword+'】' not in headings) or any(h!='【'+keyword+'】' for h in headings):
        raise SourceError('record_identity_mismatch','结果关键词与请求不一致',url=source_url)
    hits=re.search(r'結果總數[：:]\s*([\d,]+)',text)
    books=re.search(r'共\s*([\d,]+)\s*書目',text)
    # No h3 is normal on the site's explicit zero-result page. A missing h3
    # alone is never evidence of no match, authorization or a successful result.
    explicit_empty=any(re.search(r'ShowErrorMessage\(\s*([\"\'])沒有結果\1\s*,\s*([\"\'])info\2\s*\)',x.get_text()) for x in soup.select('script:not([src])'))
    source_rows=soup.find_all('h5')
    if hits and books:total=int(hits[1].replace(',',''));book_total=int(books[1].replace(',',''))
    elif explicit_empty and not source_rows:total=book_total=0
    else:raise SourceError('source_schema_changed','未识别命中数或书目数；不能从标题缺失推定零命中',url=source_url)
    if (total==0)!=(book_total==0):raise SourceError('source_schema_changed','命中数与书目数矛盾',url=source_url)
    if total==0 and source_rows:raise SourceError('source_schema_changed','零命中计数与书目记录矛盾',url=source_url)
    if explicit_empty and (total or book_total or source_rows):raise SourceError('source_schema_changed','零结果提示与返回记录矛盾',url=source_url)
    items=[];uuid=r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}'
    for h in source_rows[offset:offset+limit]:
        links=[];refs=[]
        for a in h.select('a[href]')[:2]:
            link=urljoin(BASE,a['href']);v=urlsplit(link);match=re.fullmatch('/text/book/('+uuid+')(?:/('+uuid+'))?/?',v.path)
            if v.scheme!='https' or v.hostname!='www.chant.org' or v.port not in (None,443) or v.query or v.fragment or not match:
                raise SourceError('source_schema_changed','书目链接不符合原站范围',url=source_url)
            label=a.get_text(' ',strip=True)
            if not label:raise SourceError('source_schema_changed','书目链接缺少原题名',url=source_url)
            links.append({'title':label,'url':link});refs.append((match[1],match[2],label))
        if not refs or refs[0][1] is not None:raise SourceError('source_schema_changed','结果缺少可核对书目链接',url=source_url)
        item={'location':h.get_text(' ',strip=True),'links':links,'book_id':refs[0][0],'book_title':refs[0][2]}
        if len(refs)>1 and refs[1][1]:
            if refs[1][0]!=refs[0][0]:raise SourceError('record_identity_mismatch','书目与章节链接不属于同一记录',url=source_url)
            item.update(chapter_id=refs[1][1],chapter_title=refs[1][2])
        items.append(item)
    if not source_rows and total:raise SourceError('source_schema_changed','非零结果书目位置未识别',url=source_url)
    return total,book_total,items,len(source_rows),explicit_empty

def search(keyword, limit=5, *, offset=0):
    if not isinstance(keyword, str) or not 1 <= len(keyword) <= 30 or (not keyword.isalnum()):
        raise ValueError('关键词须为1–30个文字或数字，不含空白')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为1–10')
    with requests.Session() as session:
        r = session.get(BASE + '/search/FastSearch', timeout=25)
        r.raise_for_status()
        if '[Zhejiang University]' not in BeautifulSoup(r.text, 'html.parser').get_text(' ', strip=True):
            raise RuntimeError('未识别浙大机构会话')
        r = session.get(BASE + '/result/FastSearch/' + quote(keyword, safe=''), params={'SearchConfig': 'All', 'Target': keyword, 'SearchGroup': 'Book'}, timeout=30)
        r.raise_for_status()
    matched_hits,matched_books,items,source_count,explicit_empty=parse_result(r.text,keyword,r.url,limit,offset)
    result={'source': '漢達文庫校园 IP 快速检索', 'institution': 'Zhejiang University', 'query': keyword, 'search_config': 'All', 'search_group': 'Book', 'matched_hits': matched_hits, 'matched_books': matched_books, 'source_locations': source_count, 'query_verification': 'exact response URL and result title/query heading', 'no_match_evidence': 'source explicit no-results notice' if explicit_empty else None, 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < source_count else None, 'items': items, 'note': '请求 SearchGroup=Book、SearchConfig=All；源站未回显分组，2026-11-02 将 Bone 与 Book 分组分别查询春秋、甲子均得到相同计数和首条，分组筛选是否生效未确认，不能据此推断仅限传世或包含甲骨。结果位置数与书目数不同，不可混同；每次重新获取来源结果页并本地截取书目位置，来源排序可能变化；只输出少量书目位置，不输出正文或图片；校园会话可能变化。'}
    if matched_hits==0:
        result['empty_result']=True;result['empty_reason']='no_match'
        suggested={'诗经':'詩經','论语':'論語'}.get(keyword)
        if suggested:result['suggested_queries']=[{'query':suggested,'reason':'原条件零命中；古籍检索可能区分简繁，仅作建议，没有自动替换查询。'}]
    return result
