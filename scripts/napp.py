#!/usr/bin/env python3

from netmiko import ConnectHandler
import random
import json
import click
import csv
from collections import defaultdict
import pprint as pp
import logging

hp_procurve = {
    'device_type': 'hp_procurve',
    'ip': '10.0.1.11',
    'username': 'manager',
    'password': 'Aruba123',
    'port': 22,
    'verbose': False,
}

def main():
    # create logger
    logging.basicConfig(filename='napp.log',level=logging.INFO)
    # logger = logging.getLogger('simple_example')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


    # hostfile = '/Users/mrose/DropboxAruba/305-apnames.csv'
    hostfile = 'test.csv'

    with open(hostfile) as csvfile:
        readcsv = csv.reader(csvfile, delimiter=',')
        # apnames = []
        # controllerips = []
        # for row in readcsv:
        #     apname = row[0]
        #     controllerip = row[1]
        #
        #     apnames.append(apname)
        #     controllerips.append(controllerip)
        apnames = {rows[0]:rows[1] for rows in readcsv}
        # print(apnames)


    # print(apnames)

    newapnames = defaultdict(list)
    for k, v in apnames.items():
        newapnames[v].append(k)

    get_user_ap_diff(newapnames, logger)


    # pp.pprint(newapnames)






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


def get_user_ap_diff(apnames, logger):
    exportdata = {}

    for cip, apnames in apnames.items():
        aruba_os = {
            'device_type': 'aruba_os',
            'ip': cip[1:],
            'username': 'admin',
            'password': 'Aruba123',
            'port': 22,
            'verbose': False,
        }
        # print(apnames)
        logger.info("Starting query on: %s", cip[1:])
        net_connect = ConnectHandler(**aruba_os)

        show_ap_assoc= "show ap association | include Num"
        show_usertable="show user-table | include Entries"
        ap_assoc_num_clients = net_connect.send_command(show_ap_assoc)[:-1]
        user_table_count = net_connect.send_command(show_usertable)
        user_table_count = user_table_count[1:-1]

        logger.info("show ap association command: %s", show_ap_assoc)
        # exportdata['show_ap_assoc'] = show_ap_assoc
        # print("response: ", ap_assoc_num_clients)
        logger.info("user-table command: %s", show_usertable)
        # exportdata['show_usertable'] = show_usertable
        # print("response: ", user_table_count)

        usertable = user_table_count.split(":")
        #
        # May need to use usertable[0] instead of 1 based on n/n clients. Do you want connected or total?
        #
        usertable_count = usertable[1].split("/")
        logger.info("Number of users in table: %s", usertable_count[1])
        exportdata['num_of_users'] = usertable_count[1]

        showap_count = ap_assoc_num_clients.split(":")
        logger.info("Number of client associated to APs: %s", showap_count[1])
        exportdata['num_of_clients_associated'] = showap_count[1]
        if showap_count[1] != "":
            if usertable_count[1] != "":
                diffuser = int(showap_count[1]) - int(usertable_count[1])
        logger.info("Diff between client associated and usertable: %s", diffuser)
        exportdata['diff_user_count'] = diffuser


        for apname in apnames:
            show_usertable_apname = "show user-table ap-name " + apname + " unique | include Entries"
            # print(show_usertable_apname)
            data_usertable_apname = net_connect.send_command(show_usertable_apname)
            data_usertable_apname_count = data_usertable_apname.split(':')
            # print(data_usertable_apname)

            logger.info("{},{},{}".format(cip[1:],apname, data_usertable_apname_count[1][1:]))
            exportdata['controllerip'] = cip[1:]
            exportdata[apname] = data_usertable_apname_count[1][1:]

        logger.info("Completed query on: %s", cip[1:])


    # pp.pprint(exportdata)
    with open('nordcontout.json', 'w') as outfile:
        json.dump(exportdata, outfile)

if __name__ == "__main__":
    main()
