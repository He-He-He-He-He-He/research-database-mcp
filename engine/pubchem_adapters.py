"""PubChem compound properties by name or CID through PUG-REST."""
import release_runtime
from urllib.parse import quote
import requests

def properties(identifier, kind='name'):
    if kind not in ('name', 'cid'):
        raise ValueError('kind must be name or cid')
    if not isinstance(identifier, str) or not identifier.strip() or '/' in identifier:
        raise ValueError('identifier must be a non-empty name or CID without slash')
    if kind == 'cid' and (not identifier.isdigit()):
        raise ValueError('CID must be numeric')
    path = quote(identifier, safe='')
    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/' + kind + '/' + path + '/property/MolecularFormula,MolecularWeight,InChIKey/JSON'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    items = data.get('PropertyTable', {}).get('Properties')
    if not isinstance(items, list):
        raise RuntimeError('Unexpected PubChem response')
    return {'source': 'NCBI PubChem PUG-REST', 'kind': kind, 'identifier': identifier, 'items': items, 'note': 'Compound properties; names can be ambiguous. Verify CID and chemical identity.'}
