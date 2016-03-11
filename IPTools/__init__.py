import ipv4Calc
import logging;
import math;

#logging.basicConfig(level=logging.DEBUG)

def readInput():
    print "Please input IP and netmask, empty line for end program."
    input = raw_input("IP/netmask: ").strip();
    
    logging.debug("Input: " + input);
    
    data = {"ip": 0, "netmask": 0}
    if len(input.split('/')) != 2:
        print "Format error";
        return None;
    
    ip = input.split('/')[0];
    netmask = input.split('/')[1];
    
    try:
        logging.debug("Prase IP: " + ip)
        data["ip"] = ipv4Calc.ipv4NotationToBit(ip);
        logging.debug("ip value: %s" % bin(data["ip"]));
    except:
        print "IP not vaild.";
        return None;
    
    try:
        logging.debug("Prase netmask: " + netmask)
        data["netmask"] = ipv4Calc.ipv4ConvertNetmaskToBit(netmask);
        logging.debug("netmask value: %s" % bin(data["netmask"]));
        logging.debug("invert netmask value: %s" % bin(data["netmask"] ^ ipv4Calc.makeNetMask(32)));
    except:
        print "netmask not vaild.";
        return None;
    
    return data;

while True:
    data = readInput();
    if data is None:
        break;
    ipStart = data["ip"] & data["netmask"];
    ipEnd = data["ip"] | (data["netmask"] ^ ipv4Calc.makeNetMask(32));
    
    usableStart = ipStart + 1;
    usableEnd = ipEnd - 1;
    
    print "Network: %s, netmask: %s" % (ipv4Calc.ipv4ToNotation(ipStart), ipv4Calc.ipv4ToNotation(data["netmask"])); #, math.log(data["netmask"], 2));
    print "IP range: %s - %s" % (ipv4Calc.ipv4ToNotation(ipStart), ipv4Calc.ipv4ToNotation(ipEnd));
    print "Usable IP range: %s - %s" % (ipv4Calc.ipv4ToNotation(usableStart), ipv4Calc.ipv4ToNotation(usableEnd));
    print "";