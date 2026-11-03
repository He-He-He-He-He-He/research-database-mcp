"""AI素养数据库课程列表站方默认分类，首页校内机构识别。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from zju_ai_literacy_recommendations_adapter import HOME
API = 'https://aixxsygateway.zxhnzq.com/course/website/FeaturedCourse/GetFeaturedCoursePageList'

def courses(page=1, limit=5):
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('页码须为1–1000')
    if type(limit) is not int or not 1 <= limit <= 12:
        raise ValueError('每页最多12条')
    with requests.Session() as s:
        r = s.get(HOME, timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        header = p.select_one('.header-welcome')
        if not p.title or 'AI素养与技能提升数据库' not in p.title.get_text(' ', strip=True) or (not header) or ('浙江大学' not in header.get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构首页')
        r = s.get(API, params={'page': page, 'rows': limit, 'othertype': 0, 'apptype': 1}, headers={'Referer': HOME}, timeout=25)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('站方课程列表未返回 JSON') from None
    d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(d, dict) or d.get('pageNumber') != page or d.get('pageSize') != limit or (type(d.get('total')) is not int) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('站方课程列表分页异常')
    out = []
    for row in d['list']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or (not isinstance(row.get('title'), str)):
            raise RuntimeError('课程编号或标题缺失')
        out.append({k: row.get(k) for k in ('id', 'title', 'creatorname', 'orgname', 'duration', 'profile', 'classifyname', 'topicname', 'pertype', 'islimit')})
    return {'source': 'AI素养与技能提升数据库', 'home_institution': '浙江大学', 'page': page, 'page_size': limit, 'source_total': d['total'], 'items': out[:limit], 'note': '站方课程列表默认分类（apptype=1），未确认按学校筛选，不代表全库及逐项播放权限；保留时长、权限标记原值，其单位和含义未核。未输出视频。'}
