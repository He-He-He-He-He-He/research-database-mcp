"""高校信息素养教育数据库公开课程列表；不假定当前学校订购权。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
LIBRARY = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1938'
HOME = 'https://suyang.zxhnzq.com/'
API = 'https://xxsygateway.zxhnzq.com/course/website/FeaturedCourse/GetFeaturedCoursePageList'

def courses(page=1, limit=5):
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('页码须为1–1000')
    if type(limit) is not int or not 1 <= limit <= 12:
        raise ValueError('每页最多12条')
    with requests.Session() as s:
        r = s.get(LIBRARY, timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        if not p.title or '高校信息素养教育数据库' not in p.title.get_text(' ', strip=True):
            raise RuntimeError('未确认浙大馆藏介绍')
        m = re.search('\\(试用资源\\)访问时间段\\s*[:：]\\s*(.{1,60}?)\\s*评价打分', text)
        trial = m.group(1).strip() if m else None
        r = s.get(HOME, timeout=20)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        if not p.title or '高校信息素养教育数据库' not in p.title.get_text(' ', strip=True):
            raise RuntimeError('未确认数据库官网')
        r = s.get(API, params={'page': page, 'rows': limit, 'othertype': 0, 'apptype': 1}, headers={'Referer': HOME}, timeout=25)
        r.raise_for_status()
        j = r.json()
    d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(d, dict) or d.get('pageNumber') != page or d.get('pageSize') != limit or (type(d.get('total')) is not int) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('公开课程目录分页异常')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('title'), str)):
            raise RuntimeError('课程编号或标题缺失')
        items.append({k: x.get(k) for k in ('id', 'title', 'creatorname', 'orgname', 'duration', 'profile', 'pertype', 'islimit')})
    return {'source': '高校信息素养教育数据库公开课程目录', 'institution': '未确认', 'library_trial_period_raw': trial, 'library_source': LIBRARY, 'page': page, 'page_size': limit, 'source_total': d['total'], 'items': items[:limit], 'note': '站方默认课程目录，未确认按学校筛选或逐项播放权限；馆方试用时间原样返回，是否续订以图书馆最新信息为准。时长/权限标记原值含义未核，不输出视频。'}
