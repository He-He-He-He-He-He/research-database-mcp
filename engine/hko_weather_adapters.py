"""香港天文台官方开放天气 API；只读，不缓存或推断天气。"""
import release_runtime
import argparse
import json
import requests
URL = 'https://data.weather.gov.hk/weatherAPI/opendata/weather.php'
KINDS = {'flw', 'fnd', 'rhrread', 'warnsum', 'warningInfo', 'swt'}
LANGUAGES = {'sc', 'tc', 'en'}

def weather(kind='rhrread', lang='sc', timeout=15):
    if kind not in KINDS or lang not in LANGUAGES:
        raise ValueError('不支持的数据类型或语言')
    response = requests.get(URL, params={'dataType': kind, 'lang': lang}, timeout=timeout)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, (dict, list)):
        raise ValueError('天文台响应格式异常')
    return {'source': '香港天文台开放数据', 'source_url': URL, 'data_type': kind, 'language': lang, 'data': result}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=sorted(KINDS), nargs='?', default='rhrread')
    parser.add_argument('--lang', choices=sorted(LANGUAGES), default='sc')
    args = parser.parse_args()
    print(json.dumps(weather(args.kind, args.lang), ensure_ascii=False, indent=2))
