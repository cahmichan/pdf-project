import argparse
import json
import sys
from pathlib import Path
from engine import Engine
import pymupdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', required=True)
    args = parser.parse_args()
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
    def progress(value, message):
        print(json.dumps({'event':'progress','value':value,'message':message}),flush=True)
    engine = Engine(Path(args.data_dir),progress)
    pymupdf.TOOLS.mupdf_display_errors(False)
    pymupdf.TOOLS.mupdf_display_warnings(False)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = engine.dispatch(request)
            response = {'ok':True,'result':result}
        except Exception as error:
            response = {'ok':False,'error':{'type':type(error).__name__,'message':str(error)}}
        print(json.dumps(response,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
