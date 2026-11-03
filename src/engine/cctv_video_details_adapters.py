"""按央视网视频 GUID 读取公开视频元数据，不读取视频流。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urlparse
import requests
API = 'https://api.cntv.cn/video/videoinfoByGuid'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'

def detail(guid):
    if not re.fullmatch('[0-9a-fA-F]{32}', guid):
        raise ValueError('GUID 必须为 32 位十六进制字符')
    r = requests.get(API, params={'serviceId': 'tvcctv', 'guid': guid}, headers={'User-Agent': USER_AGENT}, timeout=30)
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'api.cntv.cn':
        raise ValueError('非原站 HTTPS 跳转')
    obj = r.json()
    if not isinstance(obj, dict) or str(obj.get('vid', '')).lower() != guid.lower():
        raise ValueError(f"未取得对应视频元数据: {obj.get('msg', '响应格式变化')}")
    return {'endpoint': API, 'guid': guid, 'data': obj}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('guid')
    a = p.parse_args()
    print(json.dumps(detail(a.guid), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
