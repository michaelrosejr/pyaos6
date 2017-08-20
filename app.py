#!/usr/bin/env python3

from netmiko import ConnectHandler
import random
import json

hp_procurve = {
    'device_type': 'hp_procurve',
    'ip': '10.0.1.11',
    'username': 'manager',
    'password': 'Aruba123',
    'port': 22,
    'verbose': False,
}

aruba_os = {
    'device_type': 'aruba_os',
    'ip': '10.0.1.88',
    'username': 'admin',
    'password': 'Aruba123',
    'port': 22,
    'verbose': False,
}


def hpswitch():

    net_connect = ConnectHandler(**hp_procurve)
    output = net_connect.send_command("show arp")

    print(output)

    name = None
    for i, line in enumerate(output):
        r = random.randint(0,i)
        if not r and line.strip():
            name = line.split()[0]
    print(name)

def show_arp():

    net_connect = ConnectHandler(**aruba_os)
    output = net_connect.send_command("show arp")

    #print(output)
    output = output.split("\n",3)[3];
    output = output[:output.rfind('\n')]

    data = output.splitlines(True)
    for line in data:
        columns = line.split()
        arp = {}
        arp['ip'] = columns[1]
        arp['mac'] =  columns[2]
        arp['int'] = columns[3]
        print(json.dumps(arp))

def show_dhcp_stats():

    #
    net_connect = ConnectHandler(**aruba_os)
    output = net_connect.send_command("show ip dhcp statistics")

    output = output.split("\n",7)[7];
    output = output[:-2]

    #print(output)
    data = output.splitlines(True)
    for line in data:

        if (line.startswith('C') or line.startswith('Total') or line.startswith('NOTE') or line.isspace()):
            pass
        else:
            # print(line)
            dhcp = {}
            columns = line.split()
            dhcp['network'] = columns[0]
            dhcp['type'] = columns[1]
            dhcp['active'] =  columns[2]
            dhcp['total'] = columns[3]
            dhcp['used'] = columns[4]
            dhcp['free'] = columns[5]
            print(json.dumps(dhcp))

if __name__ == "__main__":
    show_dhcp_stats()