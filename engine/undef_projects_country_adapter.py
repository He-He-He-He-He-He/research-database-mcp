"""UN Democracy Fund project catalogue: local projects by country and start year."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://projects.undemocracyfund.org/'

def query(country, start_year_from=2000, start_year_to=2100, limit=50):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country name required')
    if any((type(x) is not int for x in (start_year_from, start_year_to, limit))) or not 1900 <= start_year_from <= start_year_to <= 2100 or (not 1 <= limit <= 100):
        raise ValueError('invalid years or limit')
    with requests.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        content = r.raw.read(5000001, decode_content=True)
    if len(content) > 5000000:
        raise ValueError('catalog exceeds size limit')
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.select_one('#projects-table')
    if table is None:
        raise ValueError('project table missing or source structure changed')
    out = []
    for row in table.select('tbody tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) != 6:
            continue
        location = cells[3].get_text(' ', strip=True)
        if location.casefold() != ('Local - ' + country.strip()).casefold():
            continue
        duration = cells[4].get_text(' ', strip=True)
        years = re.findall('\\b(?:19|20)\\d{2}\\b', duration)
        if not years or not start_year_from <= int(years[0]) <= start_year_to:
            continue
        title = cells[1].select_one('.project-title-small')
        desc = cells[1].select_one('.project-description-small')
        if title is None:
            raise ValueError('project title missing')
        out.append({'project_number': cells[0].get_text(' ', strip=True), 'title': title.get_text(' ', strip=True), 'description': desc.get_text(' ', strip=True) if desc else None, 'grantee': cells[2].get_text(' ', strip=True), 'location': location, 'duration': duration, 'start_year': int(years[0]), 'grant_amount_display': cells[5].get_text(' ', strip=True)})
    return {'source': 'United Nations Democracy Fund project catalogue', 'source_url': URL, 'scope': 'Local projects only; based on listed start year', 'total_matches': len(out), 'records': out[:limit], 'note': 'Local-country entries only, excluding regional projects that may involve the country. Listed grant is not actual spending; start year does not prove completion. Redistribution permission is not verified.'}
