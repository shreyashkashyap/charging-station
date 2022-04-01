import requests
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
from pathlib import Path
from traceback import print_tb
import requests, zipfile
import shutil, os
from io import BytesIO

AllowedActions = ['both', 'publish', 'subscribe']
for_command =None
temp=None
forfirmware= None
# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    
    print("--------------\n\n")
    dirmess=message.payload
    # using decode() + loads()  to convert to dictionary
    res_dict = json.loads(dirmess.decode('utf-8'))
    #res_dict is  in dictornary form
    global for_command
    global forfirmware
    forcommand=res_dict.get('command')
    forfirmware=res_dict.get('firmware_version')
    global temp
    base_api = "https://ikshana-api.zehntech.net/api/firmware?controller_id=xxxxx&version="
    #adding the version which is recived from cloud in new_link
    new_link = base_api+forfirmware
    # trg folder where we save code in backup
    trg = '//home//pi//reva//backup//codeBackup'
    #root_src_dir is the folder where we download the zip file from url
    root_src_dir = '/home/pi/reva/zip_download'
    #root_dst_dir is the folder where our all the code 
    root_dst_dir = 'C:\\Users\\ShreyashKashyapInter\\Desktop\\test\\firmware'
    #comapare forcommand
    if forcommand in ["OTA_UPDATE"]:
        
        print("OTA_UPATE request")
        print(new_link)
        print("--------------\n\n")
        #copy the old file
        files=os.listdir(root_dst_dir)

        # iterating over all the files in
        # the source directory
        for fname in files:
            shutil.copy2(os.path.join(root_dst_dir,fname), trg)
        
        print('\n copy done \n')
        print('Downloading started')
        #Defining the zip file URL
        url = new_link
     #   url = 'https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-zip-file.zip'

        # Split URL to get the file name
        filename = url.split('/')[-1]
        print(filename)

        # Downloading the file by sending the request to the URL
        req = requests.get(url)
        print('Downloading Completed')
        # extracting the zip file contents
        zipfile= zipfile.ZipFile(BytesIO(req.content))
        zipfile.extractall(root_src_dir)
        #zip file downloaded
        #copy the file 
        for src_dir, dirs, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    # in case of the src and dst are the same file
                    if os.path.samefile(src_file, dst_file):
                        continue
                    os.remove(dst_file)
                shutil.move(src_file, dst_dir)
            print ("succeful copy the zip in firmware folder")
        #moudle run in requirment.txt
        s= os.system('pip install -r path of requirment file')
        if s == 0 :
            
            temp = "new firmware install succefully "
        else:
            os.system('pip install -r path of old requiremnet file')
            filess=os.listdir(trg)
            for fname in filess:
                #again copy and replace the old file to folder
                shutil.copy2(os.path.join(trg,fname),root_dst_dir)
                temp = "old firmware re- install succefully"
            
        
#function used for send the message back to cloud
def publish_two():
    
    while True:
        if args.mode == 'both' or args.mode == 'publish':
            message = {}
            message['command'] =for_command
            message['version'] = forfirmware
            message['status'] =temp           
            messageJson = json.dumps(message)
            myAWSIoTMQTTClient.publish(topic, messageJson, 1)
            if args.mode == 'publish':
                print('Published topic %s: %s\n' % (topic, messageJson))
        time.sleep(10)
    
        


        
    
# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default=" ",
                    help="Message to publish")


args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = args.port
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
    publish_two()
time.sleep(20)

# Publish to the same topic in a loop forever
# loopCount = 0
# t=True
# while t:
#     if  args.mode == 'publish':
#         message = {}
#         message['action'] = args.message
#         message['sequence'] = loopCount
#         message['component']=args.message
#         message['cp_ID']=args.message
#         messageJson = json.dumps(message)
#         myAWSIoTMQTTClient.publish(topic, messageJson, 1)
#         if args.mode == 'publish':
#             print('Published topic %s: %s\n' % (topic, messageJson))
#         loopCount += 1
#         if message=="":
#             t=False
#         else:
#             t=True
#             
#     time.sleep(100)
