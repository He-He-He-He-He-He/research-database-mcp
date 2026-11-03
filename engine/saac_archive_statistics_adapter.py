"""National Archives Administration 2022–2025 annual statistical summaries."""
import release_runtime
import subprocess
from bs4 import BeautifulSoup
BASE = 'https://www.saac.gov.cn/daj/zhdt/'
FILES = {2022: ('202308/b2d8cfbede0546c68b4bfdb0889f2702', '202308/0396ea569aa648f1befd5c49bac87e6f', '202308/e135948610cf40139ed61c6d9a45c6f7'), 2023: ('202409/fd579fbcb59f4f4eae534495f2170849', '202409/a277f8b3bfe942ca88d3b7bcf6ddf120', '202409/b5dcf470e6494df1bda319760f5924c6'), 2024: ('202509/531ee455a24c42d79705c57a5be0a4ba', '202509/6cac5e5684874efcb454f860a4b94927', '202509/ddbd9dff62b147e58eb8fc5a5365a532'), 2025: ('202607/92cb18912a7349f883812dd3bbd3c2c4', '202607/bcc700c736184f9b9df8a1811348054c', '202607/0d9834f6b14a4842ba52e01f1560138b')}

def catalogue():
    return [{'year': y, 'part': i + 1, 'url': BASE + path + '.shtml'} for y, values in FILES.items() for i, path in enumerate(values)]

def report(year, part, keyword=''):
    if year not in FILES or isinstance(part, bool) or part not in (1, 2, 3):
        raise ValueError('available years 2022–2025; part 1–3')
    url = BASE + FILES[year][part - 1] + '.shtml'
    p = release_runtime.run(['/usr/bin/curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '30', url], capture_output=True, check=True)
    soup = BeautifulSoup(p.stdout, 'html.parser')
    body = soup.select_one('.pages_content')
    if body is None:
        raise ValueError('statistics body not found')
    paragraphs = [x.get_text(' ', strip=True) for x in body.select('p') if x.get_text(' ', strip=True)]
    if not paragraphs:
        raise ValueError('statistics body empty')
    return {'year': year, 'part': part, 'source_url': url, 'paragraphs': [x for x in paragraphs if keyword.casefold() in x.casefold()]}
