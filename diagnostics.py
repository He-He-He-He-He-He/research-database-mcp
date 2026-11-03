"""Small, redacted diagnostics. No network, credentials or environment dumps."""
import argparse,os,platform,re,shutil
from urllib.parse import urlsplit,urlunsplit


def safe_endpoint(url):
    parts=urlsplit(str(url));return urlunsplit((parts.scheme,parts.hostname or '',parts.path,'',''))


class InvalidArguments(ValueError):
    def __init__(self,message,usage,options):
        super().__init__(message[:1000]);self.usage=usage;self.options=options
    def as_dict(self):return {'kind':'invalid_arguments','usage':self.usage,'supported_options':self.options}


class CommandParser(argparse.ArgumentParser):
    def error(self,message):
        import sys
        parser=self
        for action in self._actions:
            if isinstance(action,argparse._SubParsersAction):
                command=sys.argv[1] if len(sys.argv)>1 else ''
                parser=action.choices.get(command,self)
        has_subparsers=any(isinstance(a,argparse._SubParsersAction) for a in parser._actions)
        usage='usage: research.py <command> [arguments]; use research_discover / research_help' if has_subparsers else ' '.join(parser.format_usage().split())
        options=[flag for action in parser._actions for flag in action.option_strings]
        raise InvalidArguments(message,usage[:1600],options)


class SourceError(RuntimeError):
    def __init__(self,kind,message,*,url=None,status=None,transport=None,code=None):
        super().__init__(message);self.details={'kind':kind}
        for key,value in {'endpoint':safe_endpoint(url) if url else None,'http_status':status,'transport':transport,'transport_code':code}.items():
            if value is not None:self.details[key]=value
    def as_dict(self):return dict(self.details)


def curl_error(code,url,stderr=''):
    if isinstance(stderr,bytes):stderr=stderr.decode('utf-8',errors='replace')
    match=re.search(r'(?:HTTP[^\n]*?|error:|returned error:)\s*(\d{3})',stderr,re.I)
    status=int(match.group(1)) if match else None
    kind={5:'proxy_error',6:'dns_error',7:'connection_error',22:'http_status',28:'network_timeout',35:'tls_error',47:'redirect_error',60:'tls_error',77:'tls_configuration_error'}.get(code,'transport_error')
    text=kind+': '+safe_endpoint(url)
    if status:text+=' (HTTP '+str(status)+')'
    return SourceError(kind,text,url=url,status=status,transport='curl',code=code)


def request_error(exc,url):
    name=type(exc).__name__
    kind={'SSLError':'tls_error','ProxyError':'proxy_error','ConnectTimeout':'network_timeout','ReadTimeout':'network_timeout','Timeout':'network_timeout','TooManyRedirects':'redirect_error','HTTPError':'http_status','ConnectionError':'connection_error','InvalidSchema':'proxy_or_transport_configuration_error'}.get(name,'request_error')
    response=getattr(exc,'response',None);status=getattr(response,'status_code',None)
    text=kind+': '+safe_endpoint(url)
    if status:text+=' (HTTP '+str(status)+')'
    return SourceError(kind,text,url=url,status=status,transport='requests')


def error_payload(exc):
    if type(exc).__module__.startswith('requests.'):
        converted=request_error(exc,getattr(getattr(exc,'request',None),'url','') or '')
        return {'error':str(converted),'diagnostics':converted.as_dict()}
    details=exc.as_dict() if hasattr(exc,'as_dict') else {'exception_type':type(exc).__name__}
    return {'error':str(exc),'diagnostics':details}


def environment_summary():
    from distribution import VERSION
    return {'package_version':VERSION,'platform':platform.system(),'python_version':platform.python_version(),'curl_available':shutil.which('curl') is not None,'proxy_environment_configured':any(os.environ.get(k) for k in ('HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','https_proxy','http_proxy','all_proxy')),'custom_ca_environment_configured':any(os.environ.get(k) for k in ('SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE'))}
