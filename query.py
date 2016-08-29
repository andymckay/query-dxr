import json
import os
import sys

from jinja2 import Environment, FileSystemLoader

import requests

cookies = os.getenv('DXR_COOKIES')


def lookup(cookies, query):
    headers = {'Accept': 'application/json'}
    query_param = {'q': query, 'limit': 1000}
    results = requests.get(
        'https://dxr.mozilla.org/addons/search', 
        data=query_param, cookies=cookies, headers=headers)
    results.raise_for_status()

    addons = {}
    addon_ids = set()
    lines = {}
    for result in results.json()['results']:
        addon_id = result['path'].split('/')[0]
        addon_ids.add(addon_id)
        lines.setdefault(addon_id, [])
        lines[addon_id].append(result)

    print 'Found: {} addons'.format(len(addon_ids))
    
    for addon_id in addon_ids:
        result = requests.get(
            'https://addons.mozilla.org/api/v3/addons/addon/{}/'.format(addon_id))
        if result.status_code != 200:
            addons[addon_id] = {
                'id': addon_id,
                'status': result.status_code,
                'data': {}
            }
            continue
        
        addons[addon_id] = {
            'id': addon_id,
            'status': result.status_code,
            'data': result.json() 
        }

    return addons, lines


def generate(query, addons, lines):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')

    sorted_addons = sorted([[(v['data'] or {}).get('weekly_downloads', 0), v] for v in addons.values()])
    sorted_addons = reversed([v for _, v in sorted_addons])

    data = {
        'lines': lines,
        'addons': sorted_addons,
        'query': query
    }

    output = template.render(data)
    open('index.html', 'w').write(output.encode('utf-8'))


if __name__=='__main__':
    if not cookies:
        raise ValueError('You must define DXR_COOKIES as an environment variable to get around addons security.')

    cookies = json.loads(cookies)
    query = sys.argv[1]
    addons, lines = lookup(cookies, query)
    #print addons
    #json.dump(addons, open('data.json', 'w'))
#    addons = json.load(open('data.json', 'r'))
    generate(query, addons, lines)