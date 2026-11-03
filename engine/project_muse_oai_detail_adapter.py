"""Official Project MUSE OAI-PMH, one article or book by known numeric ID."""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
URL = 'https://muse.jhu.edu/oai'
OAI = '{http://www.openarchives.org/OAI/2.0/}'
DC = '{http://purl.org/dc/elements/1.1/}'

def detail(article_id, timeout=20, kind='article'):
    if kind not in ('article', 'book'):
        raise ValueError('kind must be article or book')
    if not isinstance(article_id, (str, int)) or isinstance(article_id, bool) or (not re.fullmatch('[1-9][0-9]{0,9}', str(article_id))):
        raise ValueError('article_id must be a positive numeric Project MUSE article ID')
    ident = 'oai:muse.jhu.edu:/' + kind + '/' + str(article_id)
    r = requests.get(URL, params={'verb': 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': ident}, timeout=timeout)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    error = root.find(OAI + 'error')
    if error is not None:
        raise ValueError('OAI error: ' + str(error.get('code')) + ' ' + str(error.text or ''))
    header = root.find('.//' + OAI + 'header')
    metadata = root.find('.//' + OAI + 'metadata')
    if header is None or header.findtext(OAI + 'identifier') != ident or metadata is None:
        raise ValueError('unexpected OAI response')

    def vals(k):
        return [(x.text or '').strip() for x in metadata.findall('.//' + DC + k) if (x.text or '').strip()]
    return {'source': 'Project MUSE official OAI-PMH', 'source_url': URL, 'identifier': ident, 'datestamp': header.findtext(OAI + 'datestamp'), 'sets': [e.text for e in header.findall(OAI + 'setSpec')], 'title': vals('title'), 'creators': vals('creator'), 'publisher': vals('publisher'), 'date': vals('date'), 'identifiers': vals('identifier'), 'type': vals('type'), 'rights': vals('rights'), 'note': '按已知文章或图书 ID 获取一条公开题录；不支持关键词搜索，不证明浙大机构订购或全文权限。OAI 服务处于 beta，接口使用条件以官网为准。'}
