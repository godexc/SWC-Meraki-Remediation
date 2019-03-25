import config
import requests
import json
from meraki import meraki
import logging

#LOGGING INITITATED - TAKEN FROM ANAND KANANI's TBA Code #

namelogfile = 'swc_meraki.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(namelogfile)
datefmt='[%Y-%m-%d %H:%M:%S]'
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',datefmt)
handler.setFormatter(formatter)
logger.addHandler(handler)


#print(meraki.myorgaccess(config.meraki_api,suppressprint=False))
#print(meraki.getnetworklist(config.meraki_api, '796582', templateid=None, suppressprint=False))
#print(meraki.getnetworkdevices(config.meraki_api, 'L_681169443639800470', suppressprint=True))

def getOrg():
    orglist = []
    try:
        if config.meraki_api != None:
            logger.info('Get Organization Initiated')
            org = meraki.myorgaccess(config.meraki_api,suppressprint=True)
            for orgs in org:
                orglist.append(orgs['id'])
            return orglist
        else:
            logger.warning('Meraki API Key is either wrong or not provided in config.py file')
    except:
        logger.error("Couldn't retrieve the organization")
        return None

def getNetwork(orglist):
    try:
        logger.info('Organzations added to OrgList moving to Network List')
        nwlist = meraki.getnetworklist(config.meraki_api, orglist[0], templateid=None, suppressprint=True) #THAT LINE NEEDS TO BE CHANGED, NOW IT IS STATIC FOR ONE ORGANIZATION
        logger.info('Network List Has been Retrieved')
        for nw in nwlist:
            return nw['id']
    except:
        logger.error("Couldn't retrieve the Network")
        return None

def getDevices(nw):
    deviceSerialList = []
    try:
        logger.info('Searching for Devices Initated')
        devicelist = meraki.getnetworkdevices(config.meraki_api, nw, suppressprint=True)
        logger.info('Device List Has Been Retrieved')
        for devices in devicelist:
            deviceSerialList.append(devices['serial'])
        return deviceSerialList
    except:
        logger.error("Couldn't retrieve the Devices")
        return None

def getClients(sns_ip,seriallist): #seriallist IS getDevices Function
    try:
        logger.info('Search for the Client MAC with Appropriate IP Address has been started, (iterate through devices in the order of MR,MS and MX) => This can be added')
        for serial in seriallist:
            connected_endpoints = meraki.getclients(config.meraki_api, serial, timestamp=86400, suppressprint=True)
            logger.info('Clients have been gathered for %(serial)s ', {'serial' : serial})
            for endpoint in connected_endpoints:
                if endpoint['ip'] == sns_ip :
                    logger.info('Device is found connected to %(serial)s MAC Value will be returned', {'serial':serial})
                    return endpoint['mac']
                else:
                    logger.info('Client has not been found for %(serial)s ', {'serial' : serial})
    except:
        logger.error("Couldn't retrieve the Clients")
        return None

#def updateclientpolicy(apikey, networkid, clientmac, policy, policyid=None, suppressprint=False):
def remediateClient(clientmac,nw): #clientmac is getClients  and nw is getNetwork
    try:
        logger.info('Remediation Started')
        meraki.updateclientpolicy(config.meraki_api, nw, clientmac, 'blocked', policyid=None,suppressprint=True)
    except:
        logger.error("Couldn't remediate the Misbehaviouring Client")

def my_handler(event, context):
    ip = event["ips"][0]
    org = getOrg()
    nw = getNetwork(org)
    devices= getDevices(nw)
    client_mac = getClients(ip,devices)
    remediateClient(client_mac,nw)

    return {
    message : "{0} has been blocked successfully".format(ip)
    }

if __name__ == '__main__':
    org = getOrg()
    print(org)

    nw = getNetwork(org)
    print(nw)

    devices= getDevices(nw)
    print(devices)

    sns_ip = '192.168.128.19'
    client_mac = getClients(sns_ip,devices)
    print(client_mac)

    remediateClient(client_mac,nw)


"""

TRYING TO ACHIEVE AUTO REMEDIATION SCENARIO WITH MERAKI CLOUD AND STEALTHWATCH CLOUD VIA AWS LAMBDA SNS AS TRIGGER

SCENARIO 1: CATCH and BLOCK INTERNAL IP SCANNER
SCENARIO 2: CATCH and BLOCK IPs CONNECTING TO BLACKLIST COUNTRIES

DOs : LOGGER, TRY/EXPECT and ERROR MANAGEMENT

NEEDS:
-NO API ON MERAKI SIDE THAT WILL RETURN THE MAC ADDRESS OF IP THEREFORE GOING TO USE S/N OF A DEVICE

-OVERALL FLOW
def getOrg()
GET/organizations => Retrieve return output[0]['id'] as organizationId
myorgaccess(config.meraki_api,suppressprint=False)

def getNetwork()
GET/organizations/{organizationId}/networks => Retrieve return output[0]['id'] as NetworkId
def getnetworklist(apikey, orgid, templateid=None, suppressprint=False):

def getDevices()
GET/networks/[networkId]/devices => Search for output[i]['model'] startswith MX and based on that use the same i return output[i]['serial']
def getnetworkdevices(apikey, networkid, suppressprint=False):


def getClients()
GET/devices/[serial]/clients?timespan=7200 => Search for the IP Address specified in Stealthwatch Alert (SNS) for output[i]['ip']
equals SWCIP then use the same i return output[i]['mac']
def getclients(apikey, serialnum, timestamp=86400, suppressprint=False)


def remediateClient()
PUT/networks/[networkId]/clients/[mac]/policy?timespan=1800&devicePolicy=Blocked => Use the MAC that has been found on the previous stage
to set device policy as blocked

-AUTOMATED FLOW CAN BE FIRST USE GET/networks/[networkId]/devices as TO FIND ALL THE S/Ns then USE GET/devices/[serial]/clients RECURSIVELY
TO FIND APPROPRIATE MAC-IP BINDING

"""
