import requests
import json
import time
from api import get_server_state
from api import change_server_status
from getImage import imagePull
from api import wait_for_job
from globals import *

#Global variables used by multiple functions
image_to_use_uuid = ""
serverUUID = ""
server_job_uuid = ""

WAIT_TIME = 30 #seconds
MAX_NO_ATTEMPTS = 5
isVerbose = False
ENDPOINT = globalENDPOINT
username = globalUsername
customerUUID = globalCustomerUUID
password = globalPassword

#Method used to get authenication token
def getToken(endpoint, username, cust_uuid, password):
    tokenURL = "%srest/user/current/authentication" % endpoint
    apiUserName = username + "/" + cust_uuid
    tokenPayload = {'automaticallyRenew': 'True'}
    tokenRequest = requests.get(tokenURL, params=tokenPayload,
                                auth=(apiUserName, password))

    retry = True
    count = 1

    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):

        tokenRequest = requests.get(tokenURL, params=tokenPayload,
                                    auth=(apiUserName, password))
        if tokenRequest.ok:
            token = tokenRequest.content
            tokenObj = json.loads(token)
            return tokenObj['publicToken']

        if (tokenRequest.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            raise Exception("Failed contacting %s with %s (%s)" % (
                tokenURL, tokenRequest.reason, tokenRequest.status_code))

    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        raise Exception("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the imageServer")

#Method used to build a REST call to create a new server instance
def rest_create_server(auth_parms, server_name, server_po_uuid, image_uuid, cluster_uuid, vdc_uuid, cpu_count,
                       ram_amount, nics, boot_disk_po_uuid, context_script):
    createURL = auth_parms['endpoint'] + "rest/user/current/resources/server"

    #img_ret = list_image(auth_parms, image_uuid)
    #size = img_ret['size']

    server_json = {
        "resourceName": server_name,
        "productOfferUUID": server_po_uuid,
        "imageUUID": image_uuid,
        "clusterUUID": cluster_uuid,
        "vdcUUID": vdc_uuid,
        "nics" : nics,
        "cpu": cpu_count,
        "ram": ram_amount,
        "disks": [{"iso": False,
                   # "resourceName": "the disk"
                   "resourceType": "DISK",
                   "resourceUUID": boot_disk_po_uuid,
                   "size": 20,
                   "vdcUUID": vdc_uuid,
                    "productOfferUUID": boot_disk_po_uuid
                   }],
        "resourceType": "SERVER",
        "resourceMetadata": {"publicMetadata": context_script},
        # "serverCapabilities": ["CLONE", "CHILDREN_PERSIST_ON_DELETE", "CHILDREN_PERSIST_ON_REVERT"],
    }

    payload = server_json
    print(payload)
    payload_as_string = json.JSONEncoder().encode(payload)
    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    result = rest_submit_postrequest(createURL, payload_as_string, headers, auth_parms,True)
    return result


def list_image(auth_params, uuid):
    """ Get Image details """

    # Setup serach filter
    sf = { "searchFilter" :
          { "filterConditions": [{"condition": "IS_EQUAL_TO",
                                  "field": "resourceUUID",
                                  "value": [uuid]
                                 }
                                ]
          }
        }

    if (isVerbose):
        print("sf=")
        print sf
        print("---")

    result_set = rest_list_resource(auth_params, "image", sf)

    if result_set['totalCount'] == 0:
        raise RuntimeError("Image " + uuid + " not found or you do not have permissions to use it")

    print("==== Image Result ====")
    print result_set
    print("=========");
    # return just the first element (there was only one, right ?), otheriwse we end up doing e.g. img_ret['list'][0]['vdcUUID']
    # all over the place
    return result_set['list'][0]

#Method used to submit a REST POST request
def rest_submit_postrequest(theURL, payload, headers, auth_parms,create):
    retry = True
    count = 1

    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        res = requests.post(theURL, payload, auth=(auth_parms['token'], ''), headers=headers)
        print("==============================================================")
        print "Request submitted, response URL and contents:"
        print(res.url)
        print res.content

        if(create==True):
            jsonContent = json.loads(res.content)
            #Get new server UUID
            global serverUUID
            serverUUID = jsonContent["itemUUID"]
            #Get server creation job UUID
            global server_job_uuid
            server_job_uuid = jsonContent["resourceUUID"]

        print("HTTP response code: ", res.status_code)

        # Status 202 (Accepted) is good
        if ((res.status_code == 202) or (res.status_code == 200)):
            response = json.loads(res.content)
            retry = False
            return response

        if (res.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            # Something else went wrong. Pick out the status code and message
            response = json.loads(res.content)
            retry = False
            return ""
        print("==============================================================")

    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        print "HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the imageServer"
        # print(response['message'] + " (error code: " + response['errorCode'] + ")")

    return ""


def rest_list_resource(auth_parms, res_type, payload):
    print auth_parms
    theURL = auth_parms['endpoint'] + "rest/user/current/resources/" + res_type + "/list"
    print theURL

    if payload != None:
        payload_as_string = json.JSONEncoder().encode(payload);
        print("payload_as_string=" + payload_as_string)
    # Note we use data= and not params= here
    # See: http://requests.readthedocs.org/en/v1.0.1/user/quickstart/
    #
    # Also, we need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    print("theURL=" + theURL)

    retry = True
    count = 1

    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):

        if payload != None:
            res = requests.get(theURL, data=payload_as_string, auth=(auth_parms['token'], ''), headers=headers)
        else:
            res = requests.get(theURL, auth=(auth_parms['token'], ''), headers=headers)

        print("==============================================================")
        print(res.url)
        print("res=" + str(res))
        print res.content

        # Status 202 (Accepted) is good
        if (res.status_code == 200):
            response = json.loads(res.content)
            retry = False
            return response

        if (res.status_code == 429):
            print "Server busy - received 429 response, wait and retry. Attempt number: ", count
            time.sleep(WAIT_TIME)
            count = count + 1
        else:
            # Something else went wrong. Pick out the status code and message
            response = json.loads(res.content)
            print("HTTP response code: ", res.status_code)
            retry = False
            return ""

    if ((retry == True) and (count == MAX_NO_ATTEMPTS)):
        raise RuntimeError("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the imageServer")

    return ""

#Method used to build the REST request to create the new server instance
def create_server():

    token = getToken(ENDPOINT, username,
                     customerUUID, password)

    auth = dict(endpoint="https://cp.sd1.flexiant.net/", token=token)

    auth_parms = auth
    server_name = "Python Script Server test"
    server_po_uuid = "0d1a2798-91b5-35d4-93c2-fed5ece5aedd"
    cluster_uuid = "e92bb306-72cd-33a2-a952-908db2f47e98"
    vdc_uuid = "b7e36320-c08a-377d-8f7a-b9df06bca358"
    cpu_count = 4
    ram_amount = 4096
    boot_disk_po_uuid = "3660d322-9d4e-3ff7-a3bd-7b6dc635b3da"
    disk_size = 20
    context_script = ""
    networkUUID = "ce6a8dc8-bf9d-373a-8a66-888cc0c20460"
    networkType = "IP"
    resourceName = "Nic-Card-1"
    resourceType = "NIC"

    nic = {
       "clusterUUID": cluster_uuid,
       "networkUUID": networkUUID,
       "networkType": networkType,
       "resourceName": resourceName,
       "resourceType": resourceType,
       "vdcUUID": vdc_uuid,
    }

    nics = [
        nic
    ]

    print("image UUID")
    print(image_to_use_uuid)

    #Send parameters to the server
    rest_create_server(auth_parms, server_name, server_po_uuid,
                       image_to_use_uuid, cluster_uuid,
                       vdc_uuid, cpu_count,
                       ram_amount, nics, boot_disk_po_uuid, context_script)

#Methods used to change the server state to running
def start_server(auth_parms, server_uuid):
    """Function to start imageServer, uuid in server_data"""
    server_state = get_server_state(auth_parms, server_uuid)
    if server_state == 'STOPPED':
        rc = change_server_status(auth_parms=auth_parms, server_uuid=server_uuid, state='RUNNING')
        if (rc != 0):
            raise Exception("Failed to put imageServer " + server_uuid + " in to running state")

def StartVM(customerUUID, customerUsername, customerPassword, serverUUID):
    auth_client = api_session(customerUsername, customerUUID, customerPassword)
    server_state = get_server_state(auth_client, serverUUID)
    if (server_state == 'RUNNING'):
        print "Server is already running"
        return
    if (server_state == 'STOPPED' or server_state == 'STOPPING'):
        start_server(auth_client, serverUUID)
        print "Server is now RUNNING "
    else:
        print "Server could not be started because it is - %s " % server_state

def api_session(customerUsername, customerUUID, customerPassword):
    """Function to set up api session, import credentials etc."""
    token = getToken(ENDPOINT, customerUsername, customerUUID, customerPassword)
    auth_client = dict(endpoint=ENDPOINT, token=token)
    return auth_client

#Method used to create wait request for the server creation on the platform
def waitForServerCreate():
    token = getToken(ENDPOINT, username,
                     customerUUID, password)

    auth = dict(endpoint=ENDPOINT, token=token)
    auth_parms = auth
    imageWaitData = {
        "noWaitForChildren": False,
    }
    payload = imageWaitData
    createURL = ENDPOINT + "rest/user/current/resources/job/" + server_job_uuid + "/wait"
    payload_as_string = json.JSONEncoder().encode(payload)
    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    wait_for_job(createURL, payload_as_string, headers, username,customerUUID,password)

global image_to_use_uuid
image_to_use_uuid = imagePull()
if(image_to_use_uuid != ""):
    create_server()
    waitForServerCreate()
    StartVM(customerUUID,username,password,serverUUID)

else:
    raise Exception("Error: No image retrieved.")