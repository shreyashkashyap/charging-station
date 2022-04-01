
import RPi.GPIO as GPIO
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json

AllowedActions = ['both', 'publish', 'subscribe']
temp=None
for_command_id =None
for_command =None
# 
description = ""
# Custom MQTT message callback
def customCallback(client, userdata, message):
    
    
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(32,GPIO.OUT)
    print("Received a new message: ")
    print(message.payload)
    print("--------------\n\n")
    dirmess=message.payload
    # using decode() + loads()  to convert to dictionary
    res_dict = json.loads(dirmess.decode('utf-8'))
    #res_dict is  in dictornary form
    global for_command_id
    global for_command
    for_command=res_dict.get('command')
    for_command_id=res_dict.get('command_id')
    
    global temp
    global description
    if for_command in ["START_CHARGING"]:
        temp="Successfully start"
        GPIO.output(32,GPIO.LOW)
        description = "Successfully start the charging " 
        time.sleep(3)
        
    if for_command in ["STOP_CHARGING"]:
        temp="Successfully stop"
        GPIO.output(32,GPIO.HIGH)
        description = "Successfully stop the charging "
        time.sleep(3)
        
    
    if for_command not in ["STOP_CHARGING" ,"START_CHARGING"]:
        temp="ERROR"
        description = "Something went to be wrong "
        
        
    else:
        temp="Error"
        description = "something went to be wrong "
    

        
# def publish():
    
#     while True:
#         if args.mode == 'both' or args.mode == 'publish':
#             message = {}
#             message['command'] =for_command
#             message['command_id'] =for_command_id
#             message['status'] =temp
#             message['description'] = description            
#             messageJson = json.dumps(message)
#             myAWSIoTMQTTClient.publish(topic, messageJson, 1)
#             if args.mode == 'publish':
#                 print('Published topic %s: %s\n' % (topic, messageJson))
#         time.sleep(10)

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
parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!",
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
    if args.mode == 'both' or args.mode == 'publish':
        message = {}
        message['command'] =for_command
        message['command_id'] =for_command_id
        message['status'] =temp
        message['description'] = description            
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        if args.mode == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
        time.sleep(100)

    
time.sleep(2)

# Publish to the same topic in a loop forever



# while True:
#     
#     if args.mode == 'both' or args.mode == 'publish':
#         message = {}
#         
#         message['command_id'] =for_command_id
#         
#         message['sequence'] = loopCount
#         messageJson = json.dumps(message)
#         myAWSIoTMQTTClient.publish(topic, messageJson, 1)
#         if args.mode == 'publish':
#             print('Published topic %s: %s\n' % (topic, messageJson))
#         loopCount += 1
#     time.sleep(100)
