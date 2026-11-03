"""Two official 2024 Hangzhou yearbook chapter PDFs on the government cloud."""
import release_runtime
import requests
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3148/site/attach/0/'
CHAPTERS = {2: ('人口和就业人员', '5e6ca0df7ccd4a8592171e2d35e8e919.pdf'), 13: ('人民生活、物价、民政', 'c1d896778d544f668a9ebfcfb4d62fe3.pdf')}

def catalog(keyword=''):
    return [{'edition': 2024, 'chapter': n, 'title': title, 'url': BASE + filename, 'source': '杭州市统计局《杭州统计年鉴2024》'} for n, (title, filename) in CHAPTERS.items() if keyword in title]

def chapter(number):
    if isinstance(number, bool) or not isinstance(number, int) or number not in CHAPTERS:
        raise ValueError('available chapters: 2 and 13')
    item = next((x for x in catalog() if x['chapter'] == number))
    r = requests.get(item['url'], timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {**item, 'content_type': 'application/pdf', 'content': r.content}
