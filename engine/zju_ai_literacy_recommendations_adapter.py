"""浙大 AI 素养与技能数据库首页机构识别和公开推荐视频目录。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
HOME = 'https://ai.xxsuyang.com/'
API = 'https://aixxsygateway.zxhnzq.com/course/website/FeaturedCourse/GetRecommendPageList'

def recommendations(page=1, limit=5):
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('页码须为 1–1000')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('每页最多10条')
    with requests.Session() as s:
        r = s.get(HOME, timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        header = p.select_one('.header-welcome')
        if not p.title or 'AI素养与技能提升数据库' not in p.title.get_text(' ', strip=True) or (not header) or ('浙江大学' not in header.get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构首页')
        r = s.get(API, params={'page': page, 'rows': limit}, headers={'Referer': HOME}, timeout=25)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('站方课程目录未返回 JSON') from None
    d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(d, dict) or d.get('pageNumber') != page or d.get('pageSize') != limit or (type(d.get('total')) is not int) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('推荐视频分页响应异常')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('title'), str)):
            raise RuntimeError('视频编号或标题缺失')
        items.append({k: x.get(k) for k in ('id', 'title', 'creatorname', 'orgname', 'duration', 'profile', 'classifyname', 'topicname', 'pertype', 'islimit')})
    return {'source': 'AI素养与技能提升数据库', 'home_institution': '浙江大学', 'page': page, 'page_size': limit, 'source_total': d['total'], 'items': items[:limit], 'note': '首页识别浙江大学；推荐视频列表接口未确认按学校筛选，属于站方推荐子集而非全库。保留时长和权限标记原值但未核单位含义或逐条播放权限，不输出视频。'}
