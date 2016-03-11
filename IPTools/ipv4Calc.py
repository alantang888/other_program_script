import re;
import logging;

def makeNetMask(bit):
    if (bit > 32 or bit < 0):
        raise Exception;
    return (2 ** bit) - 1 << 32 - bit

def ipv4ToNotation(ipv4Address):
    if(ipv4Address >= 2 ** 32 or ipv4Address < 0):
        logging.error("IP address out of range, value: %d" % ipv4Address);
        raise Exception
    last8Bit = (2 ** 8) - 1
    
    # can't use (ipv4Address << 8) >> 24, because python auto chagne int to long
    ipPartA = (ipv4Address >> 24) & last8Bit;
    ipPartB = (ipv4Address >> 16) & last8Bit;
    ipPartC = (ipv4Address >> 8) & last8Bit;
    ipPartD = (ipv4Address >> 0) & last8Bit;
    
    return "%d.%d.%d.%d" % (ipPartA, ipPartB, ipPartC, ipPartD)

def ipv4NotationToBit(ipv4Notation):
    ipv4Regex = "^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$";
    validateResult = re.match(ipv4Regex, ipv4Notation);
    
    if validateResult is  None:
        logging.error("IP format invalid, value: %d" % ipv4Notation);
        raise Exception;
    
    ipBit = 0;
    for i in xrange(1,5):
        ipBit = ipBit | int(validateResult.group(i)) << (8 * (4 - i));
    
    return ipBit;

def ipv4NetmaskValidation(netmask):
    zeroStarted = False;
    for b in bin(ipv4NotationToBit(netmask))[-32::]:
        if b == "1" and zeroStarted == False:
            continue;
        if b == "1" and zeroStarted == True:
            return False;
        else:
            zeroStarted = True;
    return True;

def ipv4ConvertNetmaskToBit(netmask):
    netmaskBit = 0;
    
    try:
        netmask = int(netmask)
    except:
        pass;
    
    if(not isinstance(netmask, int)):
        if ipv4NetmaskValidation(netmask):
            netmaskBit = ipv4NotationToBit(netmask);
        else:
            raise Exception;
    else:
        netmaskBit = makeNetMask(netmask);
    return netmaskBit;
     

def ipv4GetNetworkName(ipv4Notation, netmask):
    return ipv4NotationToBit(ipv4Notation) & ipv4ConvertNetmaskToBit(netmask);

def ipv4InSameNetwork(ipv4Bit1, ipv4Bit2, netmask):
    return ipv4GetNetworkName(ipv4Bit1, netmask) == ipv4GetNetworkName(ipv4Bit2, netmask)
    


#print makeNetMask(0);
#print makeNetMask(1);
#8print makeNetMask(32);
#for i in range(1,33):
#    netmask = makeNetMask(i);
#    print "Bit: %d = %s = %s = %d" % (i, str(bin(netmask)), ipv4ToNotation(netmask), netmask);


if __name__ == "__main__":
    print ipv4InSameNetwork("192.168.100.1", "192.168.99.255", 21)
    print ipv4NetmaskValidation("255.255.255.0");
    print ipv4NetmaskValidation("255.255.255.240");
    print ipv4NetmaskValidation("255.255.255.241");
    print ipv4NetmaskValidation("255.255.255.255");
    print ipv4NetmaskValidation("0.0.0.0");
    print ipv4NetmaskValidation("1.0.0.0");
    print ipv4NetmaskValidation("254.0.0.0");