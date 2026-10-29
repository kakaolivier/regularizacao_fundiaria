"""Read-only local readiness check using the Python standard library."""
import argparse
import json
from urllib.request import urlopen


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=3000);args=parser.parse_args()
    base=f'http://127.0.0.1:{args.port}'
    def get(path):
        with urlopen(base+path,timeout=10) as response:
            assert response.status==200
            return response.read()
    health=json.loads(get('/api/health'));assert health['ok'] and health['runtime']=='python'
    data=json.loads(get('/api/bootstrap'));assert len(data['cases'])==health['cases']
    assert 'Território' in get('/').decode()
    for asset in ['/static/app.css','/static/app.js','/static/map.js','/static/vendor/leaflet/leaflet.js','/static/vendor/leaflet-geoman-free/leaflet-geoman.min.js']:
        assert get(asset)
    assert len(json.loads(get('/maps/goias-municipios.geojson'))['features'])==246
    if data['cases']:
        detail=json.loads(get('/api/cases/'+data['cases'][0]['id']));assert isinstance(detail['sources'],list) and isinstance(detail['documents'],list)
    print(f"READY: Python, interface, mapa local e {health['cases']} cadastros.")


if __name__=='__main__':main()
