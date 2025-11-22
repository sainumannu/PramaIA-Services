import requests, json, importlib, traceback

try:
    o = requests.get('http://localhost:8001/openapi.json', timeout=5).json()
    paths = list(o.get('paths', {}).keys())
    print('has_api_logs_path:', '/api/logs' in paths)
    for p in paths[:50]:
        print(p)
except Exception as e:
    print('openapi_error', e)

try:
    importlib.import_module('api.log_router')
    print('import_api_log_router: OK')
except Exception:
    print('import_api_log_router: ERROR')
    traceback.print_exc()
