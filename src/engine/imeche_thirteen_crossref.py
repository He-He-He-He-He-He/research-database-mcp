"""浙大馆方所列 IMechE 期刊中已核对的 18 刊 Crossref 公开题录。"""
import release_runtime
import requests
from crossref_catalog_validation import validate_crossref_page
JOURNALS = {'engine': ('International Journal of Engine Research', '1468-0874'), 'strain': ('The Journal of Strain Analysis for Engineering Design', '0309-3247'), 'a': ('Proceedings of the Institution of Mechanical Engineers Part A Journal of Power and Energy', '0957-6509'), 'b': ('Proceedings of the Institution of Mechanical Engineers Part B Journal of Engineering Manufacture', '0954-4054'), 'h': ('Proceedings of the Institution of Mechanical Engineers Part H Journal of Engineering in Medicine', '0954-4119'), 'i': ('Proceedings of the Institution of Mechanical Engineers Part I Journal of Systems and Control Engineering', '0959-6518'), 'n': ('Proceedings of the Institution of Mechanical Engineers Part N Journal of Nanoengineering and Nanosystems', '1740-3499'), 'c': ('Proceedings of the Institution of Mechanical Engineers Part C Journal of Mechanical Engineering Science', '0954-4062'), 'd': ('Proceedings of the Institution of Mechanical Engineers Part D Journal of Automobile Engineering', '0954-4070'), 'e': ('Proceedings of the Institution of Mechanical Engineers Part E Journal of Process Mechanical Engineering', '0954-4089'), 'f': ('Proceedings of the Institution of Mechanical Engineers Part F Journal of Rail and Rapid Transit', '0954-4097'), 'g': ('Proceedings of the Institution of Mechanical Engineers Part G Journal of Aerospace Engineering', '0954-4100'), 'j': ('Proceedings of the Institution of Mechanical Engineers Part J Journal of Engineering Tribology', '1350-6501'), 'k': ('Proceedings of the Institution of Mechanical Engineers Part K Journal of Multi-body Dynamics', '1464-4193'), 'l': ('Proceedings of the Institution of Mechanical Engineers Part L Journal of Materials Design and Applications', '1464-4207'), 'm': ('Proceedings of the Institution of Mechanical Engineers Part M Journal of Engineering for the Maritime Environment', '1475-0902'), 'o': ('Proceedings of the Institution of Mechanical Engineers Part O Journal of Risk and Reliability', '1748-006X'), 'p': ('Proceedings of the Institution of Mechanical Engineers Part P Journal of Sports Engineering and Technology', '1754-3371')}

def imeche_metadata(query, journal='engine', page=1, page_size=10, timeout=25):
    if journal not in JOURNALS or not isinstance(query, str) or (not query.strip()) or (len(query) > 200):
        raise ValueError('期刊或关键词无效')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零、每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    name, issn = JOURNALS[journal]
    url = f'https://api.crossref.org/journals/{issn}/works'
    r = requests.get(url, params={'query': query.strip(), 'filter': 'type:journal-article,from-pub-date:1997-01-01', 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    validate_crossref_page(d, page_size)
    rows = [{'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts'), 'journal': x.get('container-title'), 'relation': x.get('relation', {}), 'update_to': x.get('update-to', [])} for x in items]
    return {'source': 'Crossref 公开题录', 'source_url': url, 'journal': name, 'issn': issn, 'query': query.strip(), 'page': page, 'total': total, 'items': rows, 'scope': '馆方明列 18 刊中按 ISSN 核对的一刊，自 1997 年起；不代表学校机构授权或全文。', 'note': 'Crossref 为相关性搜索；期刊更名、版本和日期口径可能影响范围；撤稿状态需核验。'}
