"""UK Parliament written questions/answers and statements API."""
import release_runtime
import requests
BASE = 'https://questions-statements-api.parliament.uk/api'
PATHS = {'questions': '/writtenquestions/questions', 'statements': '/writtenstatements/statements'}

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=45, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    return r.json()

def search(query, kind='questions', skip=0, take=10):
    if kind not in PATHS or not isinstance(query, str) or (not query.strip()):
        raise ValueError('kind must be questions or statements and query must be nonempty')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (skip, take))) or skip < 0 or (not 1 <= take <= 100):
        raise ValueError('invalid pagination')
    return _get(PATHS[kind], {'searchTerm': query.strip(), 'skip': skip, 'take': take})

def detail(identifier, kind='questions'):
    if kind not in PATHS or isinstance(identifier, bool) or (not isinstance(identifier, int)) or (identifier < 1):
        raise ValueError('invalid kind or identifier')
    return _get(PATHS[kind] + '/' + str(identifier))
