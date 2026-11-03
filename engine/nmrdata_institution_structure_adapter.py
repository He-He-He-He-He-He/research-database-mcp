"""微谱数据机构会话单条结构图链接核验，不推断化学结构。"""
import release_runtime
import hashlib
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from nmrdata_institution_catalog_adapter import BASE, TURN, _identity
from nmrdata_institution_spectrum_adapter import ID

def structure(record_id, compound_name):
    if not isinstance(record_id, str) or not ID.fullmatch(record_id):
        raise ValueError('记录编号须为 UUID')
    if not isinstance(compound_name, str) or not 1 <= len(compound_name.strip()) <= 200 or re.search('[\\x00-\\x1f]', compound_name):
        raise ValueError('须提供化合物名称')
    with requests.Session() as s:
        try:
            r = s.get(TURN, timeout=20)
            r.raise_for_status()
            r = s.get(BASE + 'ChemicalSearch.aspx', timeout=20)
            r.raise_for_status()
            if not _identity(BeautifulSoup(r.content, 'html.parser')):
                raise RuntimeError('未确认浙江大学机构身份')
            r = s.get(BASE + 'data1234helpDI.aspx', params={'ccdid': "'" + record_id + "'"}, timeout=20)
            r.raise_for_status()
            page_url = urlparse(r.url)
            if page_url.scheme != 'https' or page_url.hostname != 'www.nmrdata.com' or page_url.path != '/data1234helpDI.aspx':
                raise RuntimeError('微谱结构页地址异常')
            p = BeautifulSoup(r.content, 'html.parser')
            label = p.select_one('#Label4')
            images = p.select('img[src]')
            if not label or label.get_text(' ', strip=True) != compound_name.strip() + '的结构图和碳谱：' or record_id.lower() not in r.text.lower() or (len(images) != 1):
                raise RuntimeError('结构图页面编号、名称或图片数量不一致')
            u = urlparse(urljoin(r.url, images[0]['src']))
            if u.scheme != 'https' or u.hostname != 'www.nmrdata.com' or u.port not in (None, 443) or (not re.fullmatch('/DataImages/(?:[A-Za-z0-9_-]+/\\d{4}/)?\\d+\\.(?:gif|png|jpg|jpeg)', u.path, re.I)) or u.query or u.fragment:
                raise RuntimeError('结构图地址异常')
            image_url = 'https://www.nmrdata.com' + u.path
            image = s.get(image_url, timeout=20, stream=True, allow_redirects=False)
            image.raise_for_status()
            actual = urlparse(image.url)
            if image.status_code != 200:
                raise RuntimeError('结构图请求未返回成功响应')
            if actual.scheme != 'https' or actual.hostname != 'www.nmrdata.com' or actual.path != u.path or actual.query or actual.fragment:
                raise RuntimeError('结构图返回地址不一致')
            content = bytearray()
            for chunk in image.iter_content(65536):
                content.extend(chunk)
                if len(content) > 5000000:
                    raise RuntimeError('结构图超出大小限制')
        except requests.RequestException as e:
            raise RuntimeError('微谱请求失败：' + type(e).__name__) from None
    if content[:6] in (b'GIF87a', b'GIF89a'):
        fmt = 'image/gif'
    elif content[:8] == b'\x89PNG\r\n\x1a\n':
        fmt = 'image/png'
    elif content[:3] == b'\xff\xd8\xff':
        fmt = 'image/jpeg'
    else:
        raise RuntimeError('结构图文件格式未识别')
    return {'source': '微谱数据', 'institution': '浙江大学', 'record_id': record_id, 'compound': compound_name.strip(), 'image_url': image_url, 'image_mime_detected': fmt, 'image_bytes': len(content), 'image_sha256': hashlib.sha256(content).hexdigest(), 'note': '原站标示的结构图，已核对机构、记录编号与名称并检查图片文件格式；不推断结构、立体化学或化合物身份，图像需人工核对。链接和访问状态可能变化，单条可用不代表其他图像或全文权限。'}
