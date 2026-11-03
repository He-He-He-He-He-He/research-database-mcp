"""Small Python SDK using the same gates, state, diagnostics and query engine."""
import json,os
from pathlib import Path
import release_runtime as rt

class ResearchClient:
    def __init__(self,state_dir=None):
        if state_dir is None:
            app=Path(__file__).resolve().parent.parent
            settings=app.parent.parent/'connection/sdk-settings.json'
            if app.parent.name=='apps' and settings.is_file() and not os.environ.get('RESEARCH_MCP_STATE_DIR'):
                state_dir=json.loads(settings.read_text(encoding='utf-8'))['state_dir']
        self.state_dir=Path(state_dir).expanduser().resolve() if state_dir else rt.state_root()
    def setup(self,mode=None):
        import onboarding
        with rt.using_state(self.state_dir):return onboarding.select(mode) if mode else onboarding.status()
    def query(self,command,args=None,**options):
        from research_cli import query
        with rt.using_state(self.state_dir):return query(command,args,**options)
    def batch(self,queries,**options):
        from batch_query import batch
        with rt.using_state(self.state_dir):return batch(queries,**options)
    def result(self,result_id,**options):
        from result_store import fetch
        with rt.using_state(self.state_dir):return fetch(result_id,**options)

class WorldBank:
    @staticmethod
    def get_series(countries,indicators,start,end,client=None,source=None,max_pages=4,page=1,**options):
        client=client or ResearchClient()
        countries=','.join(countries) if isinstance(countries,(list,tuple)) else countries
        indicators=','.join(indicators) if isinstance(indicators,(list,tuple)) else indicators
        args=[countries,indicators,'--start',str(start),'--end',str(end),'--max-pages',str(max_pages),'--page',str(page)]
        if source is not None:args+=['--source',str(source)]
        return client.query('wb-series',args,**options)

class Crossref:
    @staticmethod
    def search(keyword,rows=5,client=None,**options):
        return (client or ResearchClient()).query('crossref',[keyword,'--rows',str(rows)],**options)
