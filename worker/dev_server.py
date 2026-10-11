"""Loopback-only development bridge. Not packaged in the desktop release."""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from engine import Engine

ROOT=Path(__file__).resolve().parents[1]
engine=Engine(ROOT/'artifacts'/'dev-sessions')


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get('Origin') not in (None,'http://127.0.0.1:1420','http://localhost:1420'):
            self.send_error(403);return
        if self.path!='/api/pdf' or self.headers.get('Content-Type')!='application/json':
            self.send_error(400);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>1024*1024:raise ValueError('Request is too large')
            result=engine.dispatch(json.loads(self.rfile.read(length)))
            payload={'ok':True,'result':result}
        except Exception as error:
            payload={'ok':False,'error':{'message':str(error)}}
        raw=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=='/health':
            self.send_response(200);self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'OK');return
        if parsed.path!='/api/document':self.send_error(404);return
        filename=Path(parse_qs(parsed.query).get('path',[''])[0]).resolve()
        if not filename.is_relative_to(engine.sessions_dir) or filename.suffix not in ('.pdf','.png') or not filename.is_file():
            self.send_error(403);return
        raw=filename.read_bytes()
        self.send_response(200);self.send_header('Content-Type','application/pdf' if filename.suffix=='.pdf' else 'image/png');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)

    def log_message(self,*args):pass


if __name__=='__main__':
    print('Folio development PDF bridge on http://127.0.0.1:1419',flush=True)
    HTTPServer(('127.0.0.1',1419),Handler).serve_forever()
