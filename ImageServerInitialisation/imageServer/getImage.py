import logging
import requests
import json
import time
from api import wait_for_job
from globals import *

ENDPOINT=globalENDPOINT
MAX_NO_ATTEMPTS = 5
WAIT_TIME = 30

loaded_image_uuid = ""
image_job_uuid = ""

username = globalUsername
customerUUID = globalCustomerUUID
password = globalPassword

#Method used to authenticate with the platform api
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
        raise Exception("HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server")

#Method used to retrieve an image from a URL and create the image on the platform
def rest_post_image(auth_parms):
    resourceURL = "http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img"
    #resourceURL = "https://images.flexiant.com/resources/galleries/1/templates/10246/images/18405/downloads/Wordpress_32_bit_2.6rev2_flexiantkvm.qcow2.gz?downloadId=78223"
    createURL = ENDPOINT + "rest/user/current/resources/image"

    vdcUUID = "b7e36320-c08a-377d-8f7a-b9df06bca358"
    productoUUID = "3660d322-9d4e-3ff7-a3bd-7b6dc635b3da"
    imageName = "pythonScriptedTestImage"
    clusterUUID = "e92bb306-72cd-33a2-a952-908db2f47e98"
    default_user = "ubuntu"
    gen_password = True
    make_image = True
    size = 100

    #Parameters used to retrieve an image from a source
    fetchParameters = {
        "url" : resourceURL,
        "makeImage" : make_image,
        "defaultUserName" : default_user,
        "genPassword" : gen_password,
    }

    #Details of the image object which will be created on the platform
    skeletonImage = {
        "productOfferUUID" : productoUUID,
        "resourceName" : imageName,
        "vdcUUID" : vdcUUID,
        "clusterUUID" : clusterUUID,
        "size" : size,
        "defaultUser" : default_user,
        "genPassword" : gen_password,
    }

    resourceData = {
        "fetchParameters" : fetchParameters,
        "skeletonImage" : skeletonImage,
    }

    payload = resourceData
    print(payload)
    payload_as_string = json.JSONEncoder().encode(payload)
    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    result = rest_submit_postrequest(createURL, payload_as_string, headers, auth_parms)
    return result

#Method used to submit the request to the API
def rest_submit_postrequest(theURL, payload, headers, auth_parms):
    retry = True
    count = 1

    while ((count <= MAX_NO_ATTEMPTS) and (retry == True)):
        res = requests.post(theURL, payload, auth=(auth_parms['token'], ''), headers=headers)
        print("==============================================================")
        print "Request submitted, response URL and contents:"
        print(res.url)
        print res.content
        print("HTTP response code: ", res.status_code)

        #Get newly created image UUID
        jsonContent = json.loads(res.content)
        global loaded_image_uuid
        loaded_image_uuid = jsonContent["itemUUID"]

        print("IMAGE UUID")
        print(loaded_image_uuid)

        #Get UUID of job assigned to the image creation
        global image_job_uuid
        image_job_uuid = jsonContent["parentJobUUID"]

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
        print "HTTP 429 ERROR, Maximum unsuccessful attempts made to send request to the server"
        # print(response['message'] + " (error code: " + response['errorCode'] + ")")

    return ""

#Method used to complete the image retrieval process
def imagePull():
    token = getToken(ENDPOINT, username,
                     customerUUID, password)

    auth = dict(endpoint=ENDPOINT, token=token)
    auth_parms = auth
    rest_post_image(auth_parms)
    waitForImage(auth_parms)
    return loaded_image_uuid

#Method used to create a wait request for the image creation
def waitForImage(auth_parms):
    imageWaitData = {
        "noWaitForChildren" : False,
    }

    payload = imageWaitData
    createURL = ENDPOINT + "rest/user/current/resources/job/" + image_job_uuid + "/wait"
    payload_as_string = json.JSONEncoder().encode(payload)

    # Need to set the content type, because if we don't the payload is just silently ignored
    headers = {'content-type': 'application/json'}
    wait_for_job(createURL,payload_as_string,headers,username,customerUUID,password)

