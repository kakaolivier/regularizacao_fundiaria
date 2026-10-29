"""Run with Python 3.10+: python app.py. No Node.js or build step is required."""
import argparse
import os
import sys
from pathlib import Path
from threading import Timer
import webbrowser


def main():
    parser = argparse.ArgumentParser(description='Território — gestão fundiária em Python')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', '3000')))
    parser.add_argument('--data-dir', type=Path, default=None)
    parser.add_argument('--open', action='store_true', help='Abrir o navegador ao iniciar')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10 ou superior é necessário.')
    if not 1 <= args.port <= 65535:
        parser.error('A porta deve estar entre 1 e 65535.')
    try:
        from waitress import serve
        from territorio import create_app
    except ImportError as exc:
        print(f'Dependência ausente: {exc.name}. Execute: python -m pip install -r requirements.txt', file=sys.stderr)
        return 1
    app = create_app(args.data_dir)
    address = f'http://127.0.0.1:{args.port}'
    print(f'Território Python iniciado · {address}\nDados locais: {app.config["DATA_DIR"]}\nPara encerrar, pressione Ctrl+C.', flush=True)
    if args.open:
        timer = Timer(1.0, lambda: webbrowser.open(address))
        timer.daemon = True
        timer.start()
    try:
        serve(app, host='127.0.0.1', port=args.port, threads=4, max_request_body_size=26 * 1024 * 1024)
    except OSError as exc:
        print(f'Não foi possível iniciar na porta {args.port}: {exc}. Experimente --port 3001.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
