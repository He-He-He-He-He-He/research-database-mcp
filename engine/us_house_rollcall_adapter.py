"""U.S. House Clerk official XML for one recorded roll-call vote."""
import release_runtime
import xml.etree.ElementTree as ET
import requests

def get_vote(year, roll):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1990 <= year <= 2100):
        raise ValueError('year 必须为 1990 至 2100 年的整数')
    if isinstance(roll, bool) or not isinstance(roll, int) or (not 1 <= roll <= 9999):
        raise ValueError('roll 必须为 1 至 9999 的整数')
    url = f'https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > 5000000:
        raise RuntimeError('众议院投票 XML 响应过大')
    try:
        root = ET.fromstring(response.content)
        meta = root.find('vote-metadata')
        if root.tag != 'rollcall-vote' or meta is None or int(meta.findtext('rollcall-num')) != roll:
            raise ValueError('unexpected roll call response')
        fields = ('majority', 'congress', 'session', 'chamber', 'rollcall-num', 'legis-num', 'vote-question', 'vote-type', 'vote-result', 'action-date', 'action-time', 'vote-desc')
        metadata = {key: meta.findtext(key) for key in fields}
        party_totals = [{item.tag: item.text for item in party} for party in meta.findall('vote-totals/totals-by-party')]
        total_node = meta.find('vote-totals/totals-by-vote')
        totals = {item.tag: item.text for item in total_node} if total_node is not None else None
        data_node = root.find('vote-data')
        if totals is None or data_node is None:
            raise ValueError('missing vote totals or vote data')
        recorded = []
        for row in data_node.findall('recorded-vote'):
            member = row.find('legislator')
            if member is None or row.find('vote') is None:
                raise ValueError('bad vote row')
            recorded.append({'name': member.text, 'attributes': dict(member.attrib), 'vote': row.findtext('vote')})
    except (ET.ParseError, ValueError, TypeError) as exc:
        raise RuntimeError('众议院投票 XML 结构异常') from exc
    return {'source': '美国众议院书记官官方点名投票记录', 'source_url': url, 'human_page': f'https://clerk.house.gov/evs/{year}/roll{roll:03d}', 'metadata': metadata, 'totals': totals, 'party_totals': party_totals, 'recorded_votes': recorded, 'scope': '仅该次众议院点名投票，保留原始英文和官方分类；并非参议院结果，法案通过与最终生效须另查。'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('year', type=int)
    p.add_argument('roll', type=int)
    a = p.parse_args()
    print(json.dumps(get_vote(a.year, a.roll), ensure_ascii=False, indent=2))
