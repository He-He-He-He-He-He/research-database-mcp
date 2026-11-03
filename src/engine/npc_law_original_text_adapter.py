"""Read paragraph text from a law's official National People's Congress Word file."""
import release_runtime
import io, re, zipfile, xml.etree.ElementTree as ET
from urllib.parse import urlsplit, unquote, urlencode
import requests
from research import get
BASE = 'https://flk.npc.gov.cn/law-search'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def text(law_id, keyword='', limit=50, offset=0):
    if not isinstance(law_id, str) or not re.fullmatch('[a-fA-F0-9]{32}', law_id):
        raise ValueError('law ID must be 32 hexadecimal characters')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword or pagination')
    detail = get(BASE + '/search/flfgDetails', {'bbbs': law_id})
    d = detail.get('data') if isinstance(detail, dict) else None
    if detail.get('code') != 200 or not isinstance(d, dict) or d.get('bbbs', '').lower() != law_id.lower():
        raise RuntimeError('law detail missing or ID mismatch')
    path = (d.get('ossFile') or {}).get('ossWordPath')
    if not isinstance(path, str) or not re.fullmatch('prod/\\d{8}/[a-f0-9]{32}\\.docx', path):
        raise ValueError('official detail does not provide an accepted Word source')
    params = {'format': 'docx', 'bbbs': law_id, 'fileId': ''}
    download = get(BASE + '/download/pc', params)
    link = (download.get('data') or {}).get('url') if download.get('code') == 200 else None
    if not isinstance(link, str):
        raise RuntimeError('official file download unavailable')
    u = urlsplit(link)
    if u.scheme != 'https' or u.hostname != 'flkoss.obs-bj2.cucloud.cn' or u.port not in (None, 443) or u.username or u.password or (unquote(u.path) != '/' + path):
        raise RuntimeError('download host or document path does not match official detail')
    with requests.get(link, timeout=(10, 30), stream=True, allow_redirects=False) as r:
        if r.status_code != 200:
            raise RuntimeError('official Word download failed')
        content = bytearray()
        for block in r.iter_content(65536):
            content.extend(block)
            if len(content) > 10000000:
                raise ValueError('Word document exceeds 10 MB')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            info = z.getinfo('word/document.xml')
            if info.file_size > 30000000:
                raise ValueError('Word document XML exceeds 30 MB')
            root = ET.fromstring(z.read(info))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        raise RuntimeError('invalid Word document') from e
    paragraphs = []
    for n, p in enumerate(root.iter(W + 'p'), 1):
        parts = []
        for x in p.iter():
            if x.tag == W + 't':
                parts.append(x.text or '')
            elif x.tag == W + 'tab':
                parts.append('\t')
            elif x.tag in (W + 'br', W + 'cr'):
                parts.append('\n')
        value = ''.join(parts).strip()
        if value and keyword in value:
            paragraphs.append({'paragraph': n, 'text': value})
    selected = paragraphs[offset:offset + limit]
    return {'law_id': law_id, 'title': d.get('title'), 'issuer': d.get('zdjgName'), 'published': d.get('gbrq'), 'effective_date': d.get('sxrq'), 'source_status_code': d.get('sxx'), 'detail_endpoint': BASE + '/search/flfgDetails?' + urlencode({'bbbs': law_id}), 'official_download_endpoint': BASE + '/download/pc?' + urlencode(params), 'source_file_path': path, 'keyword': keyword, 'matched_paragraphs': len(paragraphs), 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(paragraphs) else None, 'paragraphs': selected, 'note': '读取官方 Word 正文段落，并非判决文书；未提取页眉页脚、图片和排版，关键词逐段匹配可能跨段遗漏。法条现行效力及修订以国家法律法规数据库与原件为准。'}
