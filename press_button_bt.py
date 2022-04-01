
import RPi.GPIO as GPIO
import time
import os

Led_pin1 = 17
Led_pin2 = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)#Button to GPIO26
GPIO.setup(Led_pin1, GPIO.OUT)  #LED to GPIO17
GPIO.setup(Led_pin2, GPIO.OUT) #led to GPIO27
GPIO.output(Led_pin2, GPIO.LOW) #intial led2 is low 

#when the user  press the button btconnect function is called to turn on the bluetooth
def btconnect():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Led_pin1, GPIO.OUT)
    GPIO.output(Led_pin1, GPIO.LOW)
    os.system("rfkill unblock bluetooth")
    os.system("systemctl start bluetooth.service")
    os.system("sudo bluetoothctl discoverable on")
    
    os.system("bluetoothctl agent NoInputNoOutput")
    os.system("sudo bluetoothctl agent NoInputNoOutput")
    blinkled()
        

    
    
#when ble device is not connected the led blink continously blink with blinkled function
def blinkled():
    while True:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Led_pin2, GPIO.OUT)
        GPIO.output(Led_pin2, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(Led_pin2,GPIO.LOW)
        time.sleep(1)
    
try:
    while True:
         button_state = GPIO.input(26)
         if button_state == False:
             GPIO.output(Led_pin2, False)
             print('Bluetooth Button pressed')
             btconnect()
             time.sleep(0.2)    
         else:
             GPIO.output(Led_pin1, False)
             
except:
    GPIO.cleanup()



