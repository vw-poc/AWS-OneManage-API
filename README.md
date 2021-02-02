Description of OneManage Script

OneManage script has two py files:
Main.py
OneManageAPI.py

OneManageAPI.py contain all the procedure and function that are used by the script.

Main.py just launch the menu procedure contain in OneManageAPI.py.

Description of the script:

Summary:
The script use the Onemanage predefined Ekinops API xml template to build API POST request and send it to the OneManage Server
For each API request there is an xml template from Ekinops.
This script only use two of them: 
    device_add.xml for adding Ekinops boxes on the OneManage Server
    device_getDetails.xml for testing the API connection to the onemanage server by reading the details of an existing Ekinops box
This script is build to be easily adapt to use the other xml template from Ekinops

Detail of the script:
When the script is launch a menu is display to choose the option.

Option A is used to test the API request to the Onemanage Server by reading the configuration of an Ekinops box. The box is defined by its Serian Number.
Option B is used to add New Ekinops Boxes and is the main option of the script.

When Option A is chosen:
 
    The script use the serial number define in the serial variable 
    The script use the following xml template for getting detail of an existing device inside the OneManage server : "device_getDetails.xml"
    The script call the procedure om_api_request to send in the correct OneManage API POST format the datas to get the details of an existing box based on the xml model and the serial number.

    

When Option B is chosen:

    The script open a csv file that contain the information about the New Ekinops boxes to add
    Each row of the csv file represent one new Ekinops box.
    The script will add the Ekinops boxes row by row
    For each row the script will take the value contain in the row to complete the variables of the Ekinops xml template for adding Ekinops boxes : "device_add.xml"
    the script call the procedure om_api_request to send in the correct OneManage API format the datas to build a new Ekinops box based on the xml model and the csv row datas.

om_api_request:
 
    Procedure arguments:
    filename, mandatory, is the xml model provide by Ekinops. For adding Ekinops box use device_add.xml
    value, mandatory, a dictionary that contain variables from the csv that will be used to fill the xml model with level1 variable
    url1, mandatory, the northbound api url of the Onemanage server.
    username, mandatory, username for API request on Onemanage Server
    pwd, mandatory, password in md5 for API request on Onemanage Server
    level2, optional (if not specified default value is false), needed if xml model has a level2 zone to specify other configuration parameters such as the device_add.xml model
    level2_tag,optional (if not specified default value is none), if level 2 parameters is present specify wich level1 xml key need level2 parameter. For example in device_add.xml model the level1 key configuration need level2 values.
    update_dict,optional (if not specified default value is empty), if level 2 parameters is present, this dictionary list the value to be set on this level2 pararameters.

    Description:
    om_api_request build a pointer to the root of the xml file and call the set_xml_value procedure to add csv value from value dictionary to the xml pointer.
    Then om_api_request the api POST request value and send it to the url of the northbound of Onemanage server.

set_xml_value:

    Procedure arguments:
    position, mandatory, root level in xml file where we find level 1 parameters
    dict_modif, mandatory, value from csv in dict format to add in xml level1 parameters
    level2,mandatory, true if level2 parameter exist somewhere in the xml file
    level2_tag, mandatory,xml parameter key that need level2 configuration parameters
    update_dict , mandatory, value to configure level2 parameter. Empty if no level2
    
    Description:
    the procedure read the xml datas and for all the tag set the value based on the datas indise dict-modif.
    If one of the xml tag has the same name as level2_tag and that level2 is true than call the procedure set_xml_level2_config to configure the level2 paramters with the update_dict values.

set_xml_level2_config:

    position,mandatory, root level in xml file where we find level 1 parameters
    i, position of the xml tag that need a level2 configuration
    update_dict, level2 values
    
    Description:
    The procedure add the level2 configuration values from update_dict to the xml tags that need it (xml pointer to position [i]).

