"""AWIN programme discovery, read-only. Credentials supplied by environment."""
import json
import os
from urllib.request import Request, urlopen


def discover():
    token = os.environ.get('AWIN_API_TOKEN')
    publisher = os.environ.get('AWIN_PUBLISHER_ID')
    if not token or not publisher or not publisher.isdigit():
        return {'status': 'configuration_required', 'advertisers': []}
    request = Request('https://api.awin.com/publishers/' + publisher + '/programmes?relationship=all', headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
    with urlopen(request, timeout=25) as response:
        records = json.load(response)
    if isinstance(records, dict):
        records = records.get('programmes', records.get('data', []))
    if not isinstance(records, list):
        raise ValueError('Unexpected Awin response')
    return {'status': 'discovered', 'advertiser_count': len(records), 'commercial_approval_automated': False}


if __name__ == '__main__':
    print(json.dumps(discover()))
