from fastapi import APIRouter
import os
import glob
import json

router = APIRouter()

NODES_DIR = os.path.join(os.path.dirname(__file__), '..', 'nodes')
EVENT_SOURCES_DIR = os.path.join(os.path.dirname(__file__), '..', 'event-sources')


def list_plugins(base_dir):
    plugins = []
    for plugin_json in glob.glob(os.path.join(base_dir, '*', 'plugin.json')):
        try:
            with open(plugin_json, encoding='utf-8') as f:
                data = json.load(f)
                plugins.append({
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'type': data.get('type'),
                    'description': data.get('description'),
                    'path': os.path.relpath(plugin_json, base_dir)
                })
        except Exception as e:
            plugins.append({'error': str(e), 'file': plugin_json})
    return plugins

@router.get('/nodes', tags=["PDK"])
def get_nodes():
    """Elenca tutti i nodi disponibili nel PDK."""
    return list_plugins(NODES_DIR)

@router.get('/event-sources', tags=["PDK"])
def get_event_sources():
    """Elenca tutti gli event sources disponibili nel PDK."""
    return list_plugins(EVENT_SOURCES_DIR)
