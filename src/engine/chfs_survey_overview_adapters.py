"""西南财经大学中国家庭金融调查公开概览。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://chfs.swufe.edu.cn/sjzx/gksjk.htm'

def chfs_overview():
    r = requests.get(URL, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    area = s.select_one('#vsb_content_2')
    if not area:
        raise ValueError('未识别 CHFS 概览')
    text = area.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('CHFS 概览过短')
    return {'url': URL, 'text': text, 'note': '仅一份公开项目概览，不是数据查询或数据下载接口；数据获取需遵循原站申请规则。'}
