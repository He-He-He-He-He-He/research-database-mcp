"""Europe PMC open-access article discovery and JATS text blocks."""
import release_runtime
import datetime, re, xml.etree.ElementTree as ET
from international_adapters import epmc_search, epmc_fulltext

def search(keyword, start, end, size=10, cursor='*'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 300:
        raise ValueError('keyword must be 1–300 characters')
    for date in (start, end):
        if not isinstance(date, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', date):
            raise ValueError('dates must be YYYY-MM-DD')
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            raise ValueError('invalid date') from None
    if start > end:
        raise ValueError('date range is reversed')
    query = f'({keyword}) AND OPEN_ACCESS:Y AND IN_EPMC:Y AND FIRST_PDATE:[{start} TO {end}]'
    j = epmc_search(query, size, cursor)
    rows = (j.get('resultList') or {}).get('result') if isinstance(j, dict) else None
    if not isinstance(rows, list) or type(j.get('hitCount')) is not int:
        raise RuntimeError('unexpected Europe PMC search response')
    return {'source': 'Europe PMC', 'query': query, 'hit_count': j['hitCount'], 'next_cursor': j.get('nextCursorMark'), 'items': rows, 'note': '来源开放获取及收录筛选不保证每条全文 XML 都可取；全文许可按文章原始声明核对。相关度排序与结果可能变化，跨请求不构成完整快照。'}

def sections(pmcid, keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 200 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    doc = epmc_fulltext(pmcid)
    root = ET.fromstring(doc['content'])
    local = lambda e: e.tag.rsplit('}', 1)[-1] if isinstance(e.tag, str) else ''

    def plain(e):
        return ' '.join(''.join(e.itertext()).split())
    title = next((plain(x) for x in root.iter() if local(x) == 'article-title'), '')
    licenses = [{'text': plain(x), 'attributes': dict(x.attrib)} for x in root.iter() if local(x) == 'license']
    blocks = []

    def walk(node, path, container):
        tag = local(node)
        if tag == 'sec':
            heading = next((plain(c) for c in node if local(c) == 'title'), '')
            path = path + ([heading] if heading else [])
        if tag == 'p':
            t = plain(node)
            if t:
                blocks.append({'type': 'paragraph', 'section': path, 'container': container, 'text': t})
            return
        if tag in ('fig', 'table-wrap'):
            container = tag
        for c in node:
            if local(c) == 'title' and tag == 'sec':
                continue
            walk(c, path, container)
    for child in root:
        if local(child) == 'body':
            walk(child, [], 'body')
        elif local(child) == 'front':
            for a in child.iter():
                if local(a) == 'abstract':
                    walk(a, ['Abstract'], 'abstract')
    q = keyword.casefold()
    matched = [b for b in blocks if q in b['text'].casefold() or any((q in s.casefold() for s in b['section']))]
    selected = matched[offset:offset + limit]
    return {'source': 'Europe PMC fullTextXML', 'source_url': f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML', 'pmcid': pmcid, 'pmcid_verified': doc['pmcid_verified'], 'title': title, 'license_statements': licenses, 'keyword': keyword, 'matched_blocks': len(matched), 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(matched) else None, 'blocks': selected, 'note': '只提取摘要及正文的 p 段落，保留章节路径与图表容器标记；表格单元格、图片、公式、补充材料和参考文献可能未完整提取。关键词逐段或标题匹配可能漏跨段信息；请依据原始 JATS 和文章许可核验。'}
