import importlib, traceback
try:
    importlib.import_module('api.log_router')
    print('IMPORT_OK')
except Exception as e:
    print('IMPORT_ERROR')
    traceback.print_exc()
