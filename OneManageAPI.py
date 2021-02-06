import requests  # Need to do a PIP install request
import csv
import json
import xmltodict
from requests.auth import HTTPDigestAuth
import urllib3
import xml.etree.ElementTree as ET
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from os import system, name
from time import sleep
from paramiko import SSHClient
from paramiko import SSHException
from paramiko import AutoAddPolicy

# define our clear function
def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

        # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def config_update(file, url, username, pwd):
    input_file = csv.DictReader(open(file))

    for row in input_file:
        serial = row['serial']
        filename = 'device_getDetails.xml'
        dict_value = {'serial': serial}
        jresp = om_api_request(filename, dict_value, url, username, pwd)
        ok_status=extract_element_from_json(jresp, ["OneManageInterface", "Results", "@Status"])
        sync = extract_element_from_json(jresp, ["OneManageInterface", "Results", "Result", "cpe", "config-sync"])
        timestamp = extract_element_from_json(jresp,
                                              ["OneManageInterface", "Results", "Result", "cpe", "provision_timestamp"])
        status = extract_element_from_json(jresp, ["OneManageInterface", "Results", "Result", "cpe", "status"])
        if ok_status[0] == 'NOK':
            error_status = extract_element_from_json(jresp, ["OneManageInterface", "Results","Result", "@Status"])
            print("Box with serial number: " + serial + " is not defined on the OneManage Server:")
            print("         "+ error_status[0])
        else:
            if timestamp[0] == None:
                print("Box with serial number: "+ serial + " is not yet registered on the OneManage Server")
            else:
                if status[0] == '1':
                    print("Box with serial number: " + serial + " has a provisioning failure, please check a manual update on OneManage")
                if status[0] == '2':
                    print("Box with serial number: " + serial + " has a provisioning in progress")
                if status[0] == '3':
                    print("Box with serial number: " + serial + " has a provisioning pending (waiting for the device to connect)")
                if sync[0] == "1" and status[0] == '0':
                    print("Box with serial number: " + serial + " is registered on the OneManage Server and config is already synchronized")
                if sync[0] == "2" and status[0] == '0':
                    filename = 'device_requestProtocolUpdate.xml'
                    dict_value = {'group': 'Demo-Group',
                                  'serial': serial,
                                  'force-configuration-update': '1',
                                  'force-software-update': '0'
                                  }
                    jresp = om_api_request(filename, dict_value, url, username, pwd)
                    print("Registered Box with serial number  " + serial + " need a config update:")
                    print(json.dumps(jresp, indent=4))
    print("Press Ctrl-C to terminate ")




def get_config_dict(data,keys,my_dict,my_update_dict):
    taglist = []
    for key in data[keys]:
        if key == 'config-tag':
            taglist = data[keys][key]
        if taglist.count(key) != 0:
            for key2 in data[keys][key]:
                 my_update_dict[key2] = data[keys][key][key2]

        else:
            if key != 'config-tag':
                my_dict[key]= data[keys][key]
    return my_dict,my_update_dict

def convert_csv_to_json(csv_file,json_file):
    data = {}
    fulldata = {}
    input_file = csv.DictReader(open(csv_file))
    for row in input_file:
        dataref = []
        refkey = ''
        mykey = 'none'
        for keys in row:
            if keys.find('*') != -1:
                mykey = (keys.split('*')[0])
                if refkey != mykey:
                    data1 = {}
                    dataref.append(mykey)
                data1[keys.split('*')[1]] = row[keys]
                data[mykey] = data1

            else:
                data[keys] = row[keys]
            refkey = mykey
            data['config-tag'] = dataref
        fulldata[row['serial']] = data
        data = {}
        print(fulldata)
    with open(json_file, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(fulldata, indent=4))

def extract_element_from_json(obj, path):
    '''
    Extracts an element from a nested dictionary or
    a list of nested dictionaries along a specified path.
    If the input is a dictionary, a list is returned.
    If the input is a list of dictionary, a list of lists is returned.
    obj - list or dict - input dictionary or list of dictionaries
    path - list - list of strings that form the path to the desired element
    '''
    def extract(obj, path, ind, arr):
        '''
            Extracts an element from a nested dictionary
            along a specified path and returns a list.
            obj - dict - input dictionary
            path - list - list of strings that form the JSON path
            ind - int - starting index
            arr - list - output list
        '''
        key = path[ind]
        if ind + 1 < len(path):
            if isinstance(obj, dict):
                if key in obj.keys():
                    extract(obj.get(key), path, ind + 1, arr)
                else:
                    arr.append(None)
            elif isinstance(obj, list):
                if not obj:
                    arr.append(None)
                else:
                    for item in obj:
                        extract(item, path, ind, arr)
            else:
                arr.append(None)
        if ind + 1 == len(path):
            if isinstance(obj, list):
                if not obj:
                    arr.append(None)
                else:
                    for item in obj:
                        arr.append(item.get(key, None))
            elif isinstance(obj, dict):
                arr.append(obj.get(key, None))
            else:
                arr.append(None)
        return arr
    if isinstance(obj, dict):
        return extract(obj, path, 0, [])
    elif isinstance(obj, list):
        outer_arr = []
        for item in obj:
            outer_arr.append(extract(item, path, 0, []))
        return outer_arr


def set_xml_level2_config(position,i,update_dict):

    str2 = '<variables>'
    for update in update_dict:
        str2 = str2 + '<variable name=\"'+update+'\">'+update_dict[update]+'</variable>'

    str2 = str2 + '</variables>'
    position[i].text = str2
    print('ici mon test:')
    print(str2)


def set_xml_value(position, dict_modif, level2, level2_tag, update_dict):
# position = for example root[0][0] for device_getDetails.xml
    i = 0
    for child in position:
        dict1 = child.attrib
        if level2:
            if dict1['Name'] == level2_tag:
                set_xml_level2_config(position, i, update_dict)
        for entry in dict_modif:
            if child.attrib.get('Name') == entry:
                dict1['Value'] = dict_modif[entry]
                position[i].attrib = dict1
        i = i + 1


def om_api_request(filename, value,url1,username,pwd, level2=False, level2_tag='none', update_dict={}):
    tree = ET.parse(filename)
    root = tree.getroot()
    set_xml_value(root[0][0], value, level2, level2_tag, update_dict)
    mystring = ET.tostring(root).decode()
    str1 = str(mystring)
    headers = {'Content-type': 'application/x-w-form-urlencoded', }
    payload = "\n<OneManageInterface Version=\"1\">\n" + str1 + "\n</OneManageInterface>\n"
    url = url1
    response = requests.request("POST", url,
                                auth=HTTPDigestAuth(username, pwd),
                                headers=headers,
                                data=payload,
                                verify=False)
    jresponse = xmltodict.parse(response.text)

    return jresponse


def menu():

    clear()
    url = 'https://OneManage.vw-poc.eu/OneManage/ExternalInterface/opi_server.php'
    username = 'admin'
    pwd = '647f8beeb4f468b9145a7fd4c3ff8516'
    file = "MyNewEkinopsBoxes.csv"
    json_file="MyNewEkinopsBoxes.json"


    print("************Welcome to OneManageAPI**************")
    print()

    choice = input("""
                      A: Get the detail of an existing device from OneManage.
                      B: Import New devices to OneManage.
                      C: Force Config Update on One Ekinops box - Once
                      D: Force Config Update on One Ekinops box - Continuous 
                      E: Convert CSV config file to Json format

                      Q: Logout.

                      Please enter your choice: """)


    if choice == "A" or choice == "a":
        print('A choice')
        print('Get the detail of an Ekinops box from OneManage Server')
        input_file = csv.DictReader(open(file))
        for row in input_file:
            print (row['serial'])
            serial = row['serial']
            filename = 'device_getDetails.xml'
            dict_value = {'serial': serial}
            jresp = om_api_request(filename, dict_value, url, username, pwd)
            print(json.dumps(jresp, indent = 4))
        try:
            print("Press Ctrl-C to go back to menu ")
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass
        menu()




    elif choice == "B" or choice == "b":
        print('B choice')
        print('Add Ekinops boxes from csv file to OneManage Server')
        filename = 'device_add.xml'
        with open(json_file) as f:
            data = json.load(f)
        for keys in data:
            my_dict={}
            my_update_dict={}
            response = get_config_dict(data, keys, my_dict, my_update_dict)
            dict_value=response[0]
            update_dict=response[1]
            jresp=om_api_request(filename, dict_value, url, username, pwd, True, 'configuration', update_dict)
            print(json.dumps(jresp, indent=4))
        try:
            print("Press Ctrl-C to go back to menu ")
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass
        menu()


    elif choice == "C" or choice == "C":
        print('C choice')
        print('Force software update of an Ekinops box from OneManage Server - Once')
        config_update(file, url, username, pwd)
        try:
            print("Press Ctrl-C to go back to menu ")
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass
        menu()

    elif choice == "D" or choice == "D":
        print('D choice')
        print('Force software update of an Ekinops box from OneManage Server - Continuous')
        try:
            while True:
                clear()
                config_update(file, url, username, pwd)
                sleep(10)
        except KeyboardInterrupt:
            pass
        menu()

    elif choice == "E" or choice == "E":
        print('E choice')
        print('Conversion of csv config file to json format has been done')
        convert_csv_to_json(file,json_file)
        try:
            print("Press Ctrl-C to go back to menu ")
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass
        menu()
    if choice == "F" or choice == "F":
        print('F choice')
        print('Restore Factory Default')
        # Connect
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            client.connect('92.103.89.94', port=2222, username='admin', password='admin2@HPE')

            # Run a command (execute PHP interpreter)
            client.exec_command(
                           'restore factory\n'
                           'y\n'
                          '\n')
            client.close()
        except SSHException as sshException:
            print("Unable to establish SSH connection: %s" % sshException)
        except Exception as ist:
            print(ist)

        print('Delete boxes from OneManage Server')
        input_file = csv.DictReader(open(file))
        for row in input_file:
            print (row['serial'])
            serial = row['serial']
            filename = 'device_delete.xml'
            dict_value = {'serial': serial}
            jresp = om_api_request(filename, dict_value, url, username, pwd)

        print('Add Ekinops boxes from csv file to OneManage Server')
        filename = 'device_add.xml'
        with open(json_file) as f:
            data = json.load(f)
        for keys in data:
            my_dict={}
            my_update_dict={}
            response = get_config_dict(data, keys, my_dict, my_update_dict)
            dict_value=response[0]
            update_dict=response[1]
            jresp=om_api_request(filename, dict_value, url, username, pwd, True, 'configuration', update_dict)
        print('Force software update of an Ekinops box from OneManage Server - Continuous')
        try:
            while True:
                clear()
                config_update(file, url, username, pwd)
                sleep(10)
        except KeyboardInterrupt:
            pass
        menu()

    elif choice == "Q" or choice == "q":
        print('Good Bye !')

    else:
        print("You must only select either A or B")
        print("Please try again")
        menu()
