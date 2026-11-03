"""Bundled sample evidence, deliberately distinct from code accessibility."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def evidence():
    path=Path(__file__).resolve().parent/'data/verified_capabilities.json'
    return json.loads(path.read_text(encoding='utf-8')).get('commands',{})

def status(command):
    entry=evidence().get(command)
    if not entry:return {'level':'not_tested','notice':'仅有代码入口；没有收录有效的实测样例，不当作已验证能力。'}
    return {'level':entry.get('level','not_tested'),'samples':entry.get('samples',[]),'scope_note':entry.get('scope_note'),'latest_observation':entry.get('latest_observation'),'notice':'样例证据仅对应所列参数、时间和环境；不是实时连通性或完整覆盖承诺。'}
