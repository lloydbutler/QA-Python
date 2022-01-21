#! /bin/python
# Name:        main.py
# Author:      Lloyd Butler
# Revision:    v1.0
# Description: CML automation script.

"""
This script is used to automate the creation of labs in CML based on user
requirements.
"""


import sys
from getpass import getpass
import configparser
import base64
import requests
import urllib3
import time


def menu(token, user):

    """ The Main Program """
    menu = """
        Menu Options
        ------------
        1. Set credentials
        2. Create new lab
        3. View Labs
        
    """

    while True:
        print(menu)
        option = input("Enter option (1-4, q=quit): ")
        if option == "1":
            createcredentials()
        elif option == "2":
            createlab(token, user['lab'])
        elif option == "3":
            showalllabs(token, user['lab'])
        elif option.lower() == "q":
            break
        else:
            print("Invalid option")

    return None

def createcredentials():
    """
    Generates config.ini on first use that stores user credentials.
    user must input user name and password as setup in CML, the
    lab address needs to be that as shown in browser.
    """
    username = input("Enter username: ")
    encoded_password = base64.b64encode(
        bytes(getpass("Enter password: "), encoding="UTF-8"))
    encoded_string = str(encoded_password, 'UTF-8')

    lab_address = input("Enter Lab address: ")

    config_create = configparser.ConfigParser()

    config_create["USER"] = {
        "username": f"{username}",
        "password": f"{encoded_string}",
        "lab": f"{lab_address}"
    }

    with open('config.ini', 'w', encoding='UTF-8') as conf:
        config_create.write(conf)
    print("Creating config, please wait...")
    time.sleep(2)


def authenticate(username, password, address):
    """
    Gets bearer token to allow API access. Token is created when corect
    username and password is stored in config.ini file.
    """

    decoded_password = base64.b64decode(password)
    password = decoded_password.decode('UTF-8')
    url = fr"https://{address}/api/v0/authenticate"
    payload = {
        'username': f'{username}',
        'password': f'{password}'
    }
    response_api = requests.request("POST", url, json=payload, verify=False,)
    return response_api.text


def createlab(token, address):
    """
    Creates a new lab in CML.
    user is to enter a name for the lab.
    """
    lab_name = input("Lab Name: ")
    url = fr"https://{address}/api/v0/labs?title={lab_name}"
    auth = {'Authorization': f'Bearer {token}'}
    response_api = requests.request("POST", url, headers=auth, verify=False)
    lab_id = response_api.json()['id']
    return lab_id


def showalllabs(token, address):
    """
    Shows user all labs that can edited with their credentials.
    List will include newly created labs and display the lab id.
    """
    url = fr"https://{address}/api/v0/labs?show_all=true"
    auth = {'Authorization': f'Bearer {token}'}
    response_api = requests.request("GET", url, headers=auth, verify=False)
    lab_id = response_api.json()
    return lab_id


def addnodes(token, lab, node, nodequantity, address):
    """
    Add nodes to selected lab.
    node data is pulled from the node database that is created
    when script first runs.
    Node labels are suffixed with a number to aid identification.
    """
    for i in range(nodequantity):

        url = fr"https://{address}/api/v0/labs/{lab}/nodes?populate_interfaces=true"
        auth = {'Authorization': f'Bearer {token}'}
        body = {
            "x": 0 + (i * 10),
            "y": 0 + (i * 10),
            "label": f"{node['data']['label']} - {i}",
            "configuration": f"{node['data']['configuration']}",
            "node_definition": f"{node['data']['node_definition']}",
            "image_definition": f"{node['data']['image_definition']}",
            "ram": None,
            "cpus": None,
            "cpu_limit": None,
            "data_volume": None,
            "boot_disk_size": None,
            "tags": [
                "string"
            ]
        }
        response_api = requests.request(
            "POST", url, headers=auth, json=body, verify=False)
        if response_api.status_code == 200:
            print(f"{node['data']['label']} - added to {lab}")


def labnodes(token, address):
    """
    Creates list of available nodes to the user and
    stores the node configuraions. This is run at the
    start of program and will only display available nodes.
    """
    node_available = []
    url = fr"https://{address}/api/v0/labs/10ace9/nodes"
    auth = {'Authorization': f'Bearer {token}'}
    response_api = requests.request("GET", url, headers=auth, verify=False)
    nodes = response_api.json()

    for i in range(len(nodes)):
        url = fr"https://{address}/api/v0/labs/10ace9/nodes/{nodes[i]}?simplified=false"
        auth = {'Authorization': f'Bearer {token}'}
        response_api = requests.request("GET", url, headers=auth, verify=False)
        node_available.append(response_api.json())

    return node_available


if __name__ == "__main__":
    urllib3.disable_warnings()
    while True:
        try:
            read_config = configparser.ConfigParser()
            read_config.read("config.ini")
            credentials = read_config["USER"]
            bearer_token = authenticate(
            credentials["username"], credentials["password"], credentials["lab"]).strip('"')
            break
        except:
            print("No config file present, please create one")
            createcredentials()
            print("Config file created")
    node_detail = labnodes(bearer_token, credentials["lab"])
    menu(bearer_token, credentials)
    sys.exit(0)
    # newlab = input("create new lab? Y/N: ")
    # if newlab == 'Y':
    #     createlab(bearer_token, credentials["lab"])
    # lab_ids = showalllabs(bearer_token, credentials["lab"])
    # print("select lab to edit: ")
    # for lab_list in range(len(lab_ids)):
    #     print(f"{lab_list} - {lab_ids[lab_list]}")
    # selection = lab_ids[int(input("select: "))]
    # print("select node to add: ")
    # for node_list in range(len(node_detail)):
    #     print(
    #         f"{node_list} - {node_detail[node_list]['data']['node_definition']}")
    # node_info = node_detail[int(input("select: "))]
    # nodenum = int(input("Number of nodes: "))
    # addnodes(bearer_token, selection, node_info, nodenum, credentials["lab"])
