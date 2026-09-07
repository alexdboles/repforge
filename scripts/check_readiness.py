"""Run from an uptime scheduler. Exit 0 when ready, 1 on outage; no credentials needed."""
import argparse
import json
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='App origin, for example https://www.therepforge.app')
    args = parser.parse_args()
    try:
        with urlopen(args.url.rstrip('/') + '/api/ready', timeout=10) as response:
            ready = response.status == 200 and json.load(response).get('status') == 'ready'
    except Exception:
        ready = False
    print('READY' if ready else 'UNAVAILABLE')
    return 0 if ready else 1

if __name__ == '__main__':
    raise SystemExit(main())
