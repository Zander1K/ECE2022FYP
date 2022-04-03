import os
import subprocess
from time import sleep
from FYP.radio import run
from gpiozero import Button
from display import Display
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime
import threading
import select

connection = False
display = Display()

# Rotary Encoder Mapping
buttonForMute = Button(16)
buttonForVolumeUp = Button(21)
buttonForVolumeDown = Button(20)
buttonForNext = Button(5)
buttonForPrev = Button(6)
buttonForSwitch = Button(12)
spotifyRunning = False

class Radio:

    def startup(self):
        # Turning on Appliance
        display.out("Alexander Radio","Powering On")

        # Waiting for connection
        while (not connection):
            display.out("Alexander Radio","Connecting to Network....")
            ipaddr = self.parse_ip()
            if len(ipaddr) > 1:
                connection = True

        # Display IP Address
        display.out("Connected to Internet","IP: " + ipaddr)
        sleep(2)

        # setup MPC when program starts running
        display.out("Loading: ","Radio Stations")
        sleep(2)
        Radio.run()

    def run(self):

        # Play MPC
        self.play()

        # Main program processing loop
        while True:
            try:

                # If Button/Output from Rotary Encoder, Carry out function
                self.displayCurrent() # Display Current Station with Current Time
                buttonForVolumeUp.when_pressed = self.increaseVolume
                buttonForVolumeDown.when_pressed = self.decreaseVolume
                buttonForMute.when_pressed = self.muteVolume
                buttonForNext.when_pressed = self.nextStation
                buttonForPrev.when_pressed = self.previousStation
                buttonForSwitch.when_pressed = self.switchSource


            except KeyboardInterrupt:
                self.stop()


########## WIFI NETWORK CHECK #################

def find_interface(self):
    find_device = "ip addr show"
    interface_parse = self.run_cmd(find_device)
    for line in interface_parse.splitlines():
        if "state UP" in line:
            dev_name = line.split(':')[1]
    return dev_name

# find an active IP on the first LIVE network device
def parse_ip(self):
    find_ip = "ip addr show %s" % interface
    ip_parse = self.run_cmd(find_ip)
    for line in ip_parse.splitlines():
        if "inet " in line:
            ip = line.split(' ')[5]
            ip = ip.split('/')[0]
    return ip

# run unix shell command, return as ASCII
def run_cmd(self,cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')

######### RADIO OPERATIONS #####################

def poweroff(self):
    os.system("sudo shutdown -h now")

def play(self):
    os.system("mpc play")

def pause(self):
    os.system("mpc pause")

def stop(self):
    os.system("mpc stop")

def nextStation(self):
    self.play()
    os.system("mpc next")
    self.speakCurrent()

def previousStation(self):
    self.play()
    os.system("mpc prev")
    self.speakCurrent()

def increaseVolume(self):
    if buttonForVolumeDown.is_pressed: 
        os.system("amixer sset Digital 3%+")
        self.displayVolume()

def decreaseVolume(self):
    if buttonForVolumeUp.is_pressed: 
        os.system("amixer sset Digital 3%-")
        self.displayVolume()
        sleep()
        self.displayCurrent()

def muteVolume(self):
    if buttonForMute.is_pressed:
        os.system("amixer set Master toggle")
        self.displayVolume()
        sleep()
        self.displayCurrent()

def displayCurrent(self):
    if spotifyRunning:
        dateTime = datetime.now().strftime('%b %d  %H:%M:%S\n')
        track = self.getSpotifyTrack()
        display.out(dateTime,track)
    else:
        dateTime = datetime.now().strftime('%b %d  %H:%M:%S\n')
        currentStation = self.run_cmd("mpc current")
        display.out(dateTime,currentStation)

# Speech Facility using eSpeak
def speakCurrent(self):
    if spotifyRunning:
        track = self.getSpotifyTrack()
        os.system("espeak -ven+f2 -k5 -s130 -a20 " + track +" --stdout | aplay")
    else:
        currentStation = self.run_cmd("mpc current")
        os.system("espeak -ven+f2 -k5 -s130 -a20 " + currentStation +" --stdout | aplay")


def displayVolume(self):
    volume = self.run_cmd("mpc volume")
    display.out("Alexander Radio",volume)

# Switch between spotify and radio
def switchSource(self):
    global spotifyRunning
    if spotifyRunning:
        os.system("killall journalctl")
        os.system("sudo systemctl stop raspotify.service")
        os.system("mpc play")
        spotifyRunning = True
    else:
        os.system("mpc stop")
        os.system("sudo systemctl start raspotify.service")
        self.startJournalWatch()
        spotifyRunning = False


########## SPOTIFY MONITORING ##############

def startJournalWatch(self):
        t = threading.Thread(target=self.followJournal)
        t.daemon = True
        t.start()

def getSpotifyTrack(self):
    args = ['journalctl', '--lines', '0', '--follow', '_SYSTEMD_UNIT=raspotify.service']
    f = subprocess.Popen(args, stdout=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    while True:
        line = f.stdout.readline()
        line = (line.strip())
        line = line.lstrip().decode('utf-8')

        if "INFO:librespot" in line:
            try:
                elements = line.split('::') 
                spotifyTrack = elements[1] 
                return spotifyTrack
            except ValueError:
                pass 
       
if __name__ == '__main__':
  Radio().startup()