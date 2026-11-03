"""Read publicly visible ORCID profile and work groups using the anonymous API.

ORCID record data is self-reported, and similarity of names is not identity proof.
Only public sections are returned; email and address fields are omitted.
"""
import release_runtime
import re
import requests
BASE = 'https://pub.orcid.org/v3.0/'

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('\\d{4}-\\d{4}-\\d{4}-\\d{3}[\\dX]', value):
        raise ValueError('ORCID must be a hyphenated identifier')
    digits = value.replace('-', '')
    total = 0
    for digit in digits[:15]:
        total = (total + int(digit)) * 2
    remainder = (12 - total % 11) % 11
    check = 'X' if remainder == 10 else str(remainder)
    if digits[-1] != check:
        raise ValueError('invalid ORCID checksum')
    return value

def _fetch(identifier, section):
    identifier = _id(identifier)
    with requests.get(BASE + identifier + '/' + section, headers={'Accept': 'application/json'}, timeout=(10, 30), stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200:
            raise RuntimeError('ORCID returned unexpected status')
        content = bytearray()
        for block in response.iter_content(65536):
            content.extend(block)
            if len(content) > 15000000:
                raise ValueError('ORCID response exceeds 15 MB')
    import json
    try:
        data = json.loads(content)
    except ValueError:
        raise RuntimeError('ORCID returned non-JSON') from None
    if not isinstance(data, dict) or data.get('path') not in (f'/{identifier}/{section}', f'/{identifier}'):
        raise RuntimeError('ORCID returned unexpected record')
    return (identifier, data)

def person(identifier):
    identifier, data = _fetch(identifier, 'person')
    fields = ('last-modified-date', 'name', 'other-names', 'biography', 'researcher-urls', 'keywords', 'external-identifiers')
    return {'source': 'ORCID public registry', 'orcid': identifier, 'person': {key: data[key] for key in fields if key in data}, 'note': 'Only public profile fields; email and address are omitted. Self-reported record; check identity and affiliations independently.'}

def works(identifier, offset=0, limit=20):
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('offset must be non-negative; limit must be 1–100')
    identifier, data = _fetch(identifier, 'works')
    groups = data.get('group')
    if not isinstance(groups, list):
        raise RuntimeError('ORCID returned invalid work groups')
    return {'source': 'ORCID public registry', 'orcid': identifier, 'last_modified': data.get('last-modified-date'), 'offset': offset, 'limit': limit, 'total_groups': len(groups), 'groups': groups[offset:offset + limit], 'note': 'Public work groups only; pagination is local after fetching all groups. Records may contain duplicate versions and are self-reported; not a complete publication list.'}
