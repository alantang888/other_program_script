#!/opt/ActivePython-2.7/bin/python
import sys
import logging
import dns.resolver
import GeoIP
import SocketServer

countryRelay = {"HK": "1.1.1.1", "CN": "2.2.2.2"}

DEFAULT = "HK"
LISTEN_PORT = 2527

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', filename="/dev/null")
# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', filename = "/tmp/log.txt")

gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE | GeoIP.GEOIP_CHECK_CACHE)


def getCountryByIp(ipAddress):
    countryCode = gi.country_code_by_addr(ipAddress.strip())
    logging.info("Got IP: {}, resolved country code: {}".format(ipAddress, countryCode))
    return countryCode


def getDomain(emailAddress):
    splitedAddress = emailAddress.split('@')
    if(len(splitedAddress) != 2):
        logging.error("email address invalid: ".format(emailAddress))
        raise Exception("email address invalid.")
    domain = splitedAddress[1]
    logging.info("Got email address: {}, domain: {}".format(emailAddress, domain))
    return domain


def getMx(domainName):
    logging.info("Query MX record for {}".format(domainName))
    ans = dns.resolver.query(domainName, "mx")
    return sorted(list(ans), key=lambda x: x.preference)


def getIpFromRecord(dnsRecord):
    ipAddress = str(dns.resolver.query(dnsRecord.exchange)[0])
    logging.info("Got record: {}, resolved IP: {}, type: {}".format(str(dnsRecord.exchange), ipAddress, type(ipAddress)))
    return ipAddress


def genReplyPostfix(destination):
    return "200 relay:[{}]\n".format(destination)


def getResult(email):
    countryCode = DEFAULT
    try:
        domain = getDomain(email.strip())
        mxRecords = getMx(domain)

        for record in mxRecords:
            try:
                ip = getIpFromRecord(record)
                countryCode = getCountryByIp(ip)
                logging.info("Got country code: {}".format(countryCode))
                break
            except:
                continue
    except:
        logging.info("Except found: {}".format(sys.exc_info()[0]))
    finally:
        return genReplyPostfix(countryRelay.get(countryCode, countryRelay[DEFAULT]))


class LookupRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        #print("new connection.")
        while True:
            self.data = self.request.recv(1024).strip()
            if not self.data:
                break
            self.request.sendall(getResult(self.data))

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # For Thread share port
    allow_reuse_address = True


# main program start
if __name__ == "__main__":
    # print getResult(sys.stdin.readline())
    server = ThreadedTCPServer(("0.0.0.0", LISTEN_PORT), LookupRequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        logging.info("Server shutdown by Keyboard Interrupt")
