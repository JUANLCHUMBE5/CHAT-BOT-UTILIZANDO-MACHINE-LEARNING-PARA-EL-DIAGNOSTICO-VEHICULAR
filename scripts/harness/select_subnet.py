"""Select an unused /24 without removing any existing Docker network."""
import ipaddress
import json
import subprocess
import sys

ids = subprocess.check_output(['docker', 'network', 'ls', '-q'], text=True).split()
networks = json.loads(subprocess.check_output(['docker', 'network', 'inspect', *ids], text=True)) if ids else []
used = [ipaddress.ip_network(c['Subnet']) for n in networks
        for c in (n.get('IPAM', {}).get('Config') or []) if c.get('Subnet')]
used.extend(ipaddress.ip_network(value) for value in sys.argv[1:])
for candidate in ipaddress.ip_network('10.253.0.0/16').subnets(new_prefix=24):
    if not any(candidate.overlaps(n) for n in used if n.version == 4):
        print(candidate)
        break
else:
    raise RuntimeError('No isolated subnet available; never prune networks automatically')


