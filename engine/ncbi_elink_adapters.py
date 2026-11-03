"""NCBI ELink single-input ID relationships via a specified link name."""
import release_runtime
import re
from ncbi_entrez_adapters import _get

def links(identifier, linkname):
    if isinstance(identifier, bool) or not str(identifier).isdigit():
        raise ValueError('identifier must be numeric')
    if not isinstance(linkname, str) or not re.fullmatch('[a-z0-9]+(?:_[a-z0-9]+)+', linkname):
        raise ValueError('linkname must be an NCBI ELink name such as pubmed_pmc')
    source = linkname.split('_', 1)[0]
    data = _get('elink', {'id': str(identifier), 'dbfrom': source, 'linkname': linkname})
    if not isinstance(data.get('linksets'), list) or len(data['linksets']) != 1:
        raise RuntimeError('Unexpected ELink response')
    result = data['linksets'][0]
    return {'source': 'NCBI ELink', 'input_id': str(identifier), 'linkname': linkname, 'linksets': result.get('linksetdbs', []), 'note': 'Only NCBI indexed links; PMCID link presence does not necessarily establish reuse rights.'}
