"""UN Security Council consolidated sanctions XML: exact reference lookup."""
import release_runtime
import xml.etree.ElementTree as ET
import requests
SOURCE = 'https://scsanctions.un.org/resources/xml/en/name/consolidated.xml'

def load():
    response = requests.get(SOURCE, timeout=45, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    response.raise_for_status()
    root = ET.fromstring(response.content)
    if root.tag != 'CONSOLIDATED_LIST' or root.find('INDIVIDUALS') is None or root.find('ENTITIES') is None:
        raise ValueError('Unexpected UN consolidated XML structure')
    return root

def counts(root):
    return {'date_generated': root.get('dateGenerated'), 'individuals': len(root.findall('./INDIVIDUALS/INDIVIDUAL')), 'entities': len(root.findall('./ENTITIES/ENTITY')), 'source_url': SOURCE}

def reference(root, ref):
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError('reference number must be nonempty')
    ref = ref.strip().casefold()
    matches = [record for group in ('INDIVIDUALS/INDIVIDUAL', 'ENTITIES/ENTITY') for record in root.findall('./' + group) if (record.findtext('REFERENCE_NUMBER') or '').strip().casefold() == ref]
    return [{'record_type': record.tag, 'reference_number': record.findtext('REFERENCE_NUMBER'), 'source_xml': ET.tostring(record, encoding='unicode')} for record in matches]
