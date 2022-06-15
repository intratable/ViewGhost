#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
from requests import get
import subprocess
import time
import signal
import webbrowser, time
import re
import sys
from stem import Signal
from stem.control import Controller
from packaging import version

IP_API = "https://api.ipify.org/?format=json"

#LATEST_RELEASE_API =

VERSION = "ACAB스키"

class bcolors:

    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[31m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BGRED = '\033[41m'
    WHITE = '\033[37m'

def t():
    current_time = time.localtime()
    ctime = time.strftime('%H:%M:%S', current_time)
    return '[' + ctime + ']'

def sigint_handler(signum, frame):
    print("User interrupt ! shutting down")
    stop_viewghost()

def logo():
    os.system('clear')
    print(bcolors.RED + bcolors.BOLD)
    print("""

██╗░░░██╗██╗███████╗░██╗░░░░░░░██╗░██████╗░██╗░░██╗░█████╗░░██████╗████████╗
██║░░░██║██║██╔════╝░██║░░██╗░░██║██╔════╝░██║░░██║██╔══██╗██╔════╝╚══██╔══╝
╚██╗░██╔╝██║█████╗░░░╚██╗████╗██╔╝██║░░██╗░███████║██║░░██║╚█████╗░░░░██║░░░
░╚████╔╝░██║██╔══╝░░░░████╔═████║░██║░░╚██╗██╔══██║██║░░██║░╚═══██╗░░░██║░░░
░░╚██╔╝░░██║███████╗░░╚██╔╝░╚██╔╝░╚██████╔╝██║░░██║╚█████╔╝██████╔╝░░░██║░░░
░░░╚═╝░░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝░╚════╝░╚═════╝░░░░╚═╝░░░
    
    
    """.format(V=VERSION))
    print(bcolors.ENDC)

#logo()
#lte = str(input('Network adapter :')) 
#os.system('clear')

def usage():

    logo()
    
    print("""
    Viewghost usage:
    -s    --start       Start Viewghost
    -x    --stop        Stop  Viewghost
    -u    --update      check for update
    -h	  --help	Help..
    -e    --exit        Exit..

    """)

def ip():
    while True:
        try:
            jsonRes = get(IP_API).json()
            ipTxt = jsonRes["ip"]
        except:
            continue
        break
    return ipTxt

def check_root():
    if os.geteuid() != 0:
        print("You must be root; Say the magic word 'sudo'")
        sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

TorrcCfgString = \
    """
VirtualAddrNetwork 10.0.0.0/10
AutomapHostsOnResolve 1
TransPort 9040
DNSPort 5353
ControlPort 9051
RunAsDaemon 1
"""

resolvString = 'nameserver 127.0.0.1'

Torrc = '/etc/tor/torghostrc'
resolv = '/etc/resolv.conf'

def start_viewghost(): 
    logo()
    os.system('sudo cp /etc/resolv.conf /etc/resolv.conf.bak')
    if os.path.exists(Torrc) and TorrcCfgString in open(Torrc).read():
        print(t() + ' Torrc file already configured')
    else:

        with open(Torrc, 'w') as myfile:
            print(t() + ' Writing torcc file ')
            myfile.write(TorrcCfgString)
            print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    if resolvString in open(resolv).read():
        print(t() + ' DNS resolv.conf file already configured')
    else:
        with open(resolv, 'w') as myfile:
            print(t() + ' Configuring DNS resolv.conf file.. '),
            myfile.write(resolvString)
            print(bcolors.GREEN + '[done]' + bcolors.ENDC)

    print(t() + ' Stopping tor service '),
    os.system('sudo systemctl stop tor')
    os.system('sudo fuser -k 9051/tcp > /dev/null 2>&1')
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' Starting new tor daemon '),
    os.system('sudo -u debian-tor tor -f /etc/tor/torghostrc > /dev/null'
              )
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' setting up iptables rules'),

    iptables_rules = \
        """
	NON_TOR="192.168.1.0/24 192.168.0.0/24"
	TOR_UID=%s
	TRANS_PORT="9040"

	iptables -F
	iptables -t nat -F

	iptables -t nat -A OUTPUT -m owner --uid-owner $TOR_UID -j RETURN
	iptables -t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353
	for NET in $NON_TOR 127.0.0.0/9 127.128.0.0/10; do
	 iptables -t nat -A OUTPUT -d $NET -j RETURN
	done
	iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports $TRANS_PORT

	iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
	for NET in $NON_TOR 127.0.0.0/8; do
	 iptables -A OUTPUT -d $NET -j ACCEPT
	done
	iptables -A OUTPUT -m owner --uid-owner $TOR_UID -j ACCEPT
	iptables -A OUTPUT -j REJECT
	""" \
        % subprocess.getoutput('id -ur debian-tor')

    os.system(iptables_rules)
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' Fetching current IP...')
    print(t() + ' CURRENT IP : ' + bcolors.GREEN + ip() + bcolors.ENDC)

def stop_viewghost():
    logo()
    mac_reset()
    print(bcolors.RED + t() + 'STOPPING Viewghost' + bcolors.ENDC)
    print(t() + ' Flushing iptables, resetting to default'),
    os.system('mv /etc/resolv.conf.bak /etc/resolv.conf')
    IpFlush = \
        """
	iptables -P INPUT ACCEPT
	iptables -P FORWARD ACCEPT
	iptables -P OUTPUT ACCEPT
	iptables -t nat -F
	iptables -t mangle -F
	iptables -F
	iptables -X
	"""
    os.system(IpFlush)
    os.system('sudo fuser -k 9051/tcp > /dev/null 2>&1')
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' Restarting Network manager'),
    os.system('service network-manager restart')
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' Fetching current IP...')
    time.sleep(2)
    print(t() + ' CURRENT IP : ' + bcolors.GREEN + ip() + bcolors.ENDC)
    time.sleep(2)
    logo()
    time.sleep(2)
    sys.exit(2) 

def switch_tor():
    logo()
    print(t() + ' Please wait...')
    time.sleep(5)
    print(t() + ' Requesting new circuit...'),
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
    print(bcolors.GREEN + '[done]' + bcolors.ENDC)
    print(t() + ' Fetching current IP...')
    print(t() + ' CURRENT IP : ' + bcolors.GREEN + ip() + bcolors.ENDC)



def start_v():
    
    logo()
    #check_update()
    ante = input('Network Adapter eth0 || wlan0 : ')

    webghost = input("Enter URL :")
    print("Searching...")
    time.sleep(2)
    print("OK [✓]")
    logo()
    ghosting = input('Views :')
    time.sleep(1)
    s = input("""
    Seconds :""")
    os.system('clear')
    start_viewghost()
    f = 0 
    
    while f <= ghosting:
        
        print ("Viewings :"+f)

        mac_of = subprocess.Popen(["ifconfig %s" %ante, " down"], stdout=subprocess.PIPE, shell=True)
        switch =subprocess.Popen(["macchanger -r%s" %ante, ""], stdout=subprocess.PIPE, shell=True)
        mac_on = subprocess.Popen(["ifconfig %s" %ante, " up"], stdout=subprocess.PIPE, shell=True)
        (mac_of, err) = mac_of.communicate()
        mac_of = mac_of.split()
        (mac_on, err) = mac_on.communicate()
        mac_on = mac_on.split()
        (switch, err) = switch.communicate()
        switch = switch.split()
       
        os.system('clear')
        time.sleep(1)
        webbrowser.open_new(webghost)
        time.sleep(int(s))
        os.system('clear')        
        switch_tor()
        time.sleep(2)
        os.system('clear')
        f += 1

def mac_reset(ante) :

    mac_of = subprocess.Popen(["ifconfig %s" %ante, " down"], stdout=subprocess.PIPE, shell=True)
    reset =subprocess.Popen(["macchanger -p%s" %ante, ""], stdout=subprocess.PIPE, shell=True)
    mac_on = subprocess.Popen(["ifconfig %s" %ante, " up"], stdout=subprocess.PIPE, shell=True)
    (mac_of, err) = mac_of.communicate()
    mac_of = mac_of.split()
    (mac_on, err) = mac_on.communicate()
    mac_on = mac_on.split()
    (reset, err) = reset.communicate()
    reset = reset.split()
    
""""
def check_update():
    print(t() + ' Checking for update...')
    jsonRes = get(LATEST_RELEASE_API).json()
    newversion = jsonRes["tag_name"][1:]
    print(newversion)
    if version.parse(newversion) > version.parse(VERSION):
        print(t() + bcolors.GREEN + ' New update available!' + bcolors.ENDC)
        print(t() + ' Your current ViewGhost version : ' + bcolors.GREEN + VERSION + bcolors.ENDC)
        print(t() + ' Latest ViewGhost version available : ' + bcolors.GREEN + newversion + bcolors.ENDC)
        yes = {'yes', 'y', 'ye', ''}
        no = {'no', 'n'}

        choice = input(
            bcolors.BOLD + "Would you like to download latest version and build from Git repo? [Y/n]" + bcolors.ENDC).lower()
        if choice in yes:
            os.system(
                'cd /tmp && git clone  https://github.com/')
            os.system('cd /tmp/torghost && sudo ./build.sh')
        elif choice in no:
            print(t() + " Update aborted by user")
        else:
            print("Please respond with 'yes' or 'no'")
    else:
        print(t() + " ViewGhost is up to date!")
 """



def main():
    check_root()
    if len(sys.argv) <= 1:
        #check_update()
        usage()
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'srxhu', [
            'start', 'stop', 'switch', 'help', 'update'])
    except (getopt.GetoptError):
        usage()
        sys.exit(2)
    for (o, a) in opts:
        if o in ('-h', '--help'):
            usage()
        elif o in ('-s', '--start'):
            start_v()
        elif o in ('-x', '--stop'):
            stop_viewghost()
        elif o in ('-e', '--exit'):
            pass
        elif o in ('-u', '--update'):
            #check_update()
            pass
        else:
            usage()




if __name__ == '__main__':
    main()
