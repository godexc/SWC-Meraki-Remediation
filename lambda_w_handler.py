'''

    _    _ _   ____            _               _____
   / \  | | | / ___|  ___  ___(_)_ __   __ _  | ____|   _  ___
  / _ \ | | | \___ \ / _ \/ _ \ | '_ \ / _` | |  _|| | | |/ _ \
 / ___ \| | |  ___) |  __/  __/ | | | | (_| | | |__| |_| |  __/
/_/   \_\_|_| |____/ \___|\___|_|_| |_|\__, | |_____\__, |\___|
                                       |___/        |___/

'''



import config
import json
from meraki import meraki
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def getOrg():
    orglist = []
    try:
        if config.meraki_api != None:
            logger.info('Get Organization Initiated')
            org = meraki.myorgaccess(config.meraki_api,suppressprint=True)
            if org != None:
                for orgs in org:
                    orglist.append(orgs['id'])
                logger.info('Organizations Returned')
                return orglist
            else:
                logger.info('Organization List is Empty')
                return None
    except Exception as err:
        logger.error("ERROR in Getting Organization", exc_info=True)
        return ("ERROR in Getting Organization" + str(err))

def getNetwork(orglist):
    try:
        logger.info('Organzations added to OrgList moving to Network List')
        nwlist = meraki.getnetworklist(config.meraki_api, orglist[0], templateid=None, suppressprint=True) #THAT LINE NEEDS TO BE CHANGED, NOW IT IS STATIC FOR ONE ORGANIZATION
        if nwlist != None:
            logger.info('Network List Has been Retrieved')
            for nw in nwlist:
                return nw['id']
        else:
            logger.info('Network List is Empty')
            return None
    except Exception as err:
        logger.error("ERROR in Getting Network", exc_info=True)
        return ("ERROR in Getting Network" + str(err))

def getDevices(nw):
    deviceSerialList = []
    try:
        logger.info('Searching for Devices Initated')
        devicelist = meraki.getnetworkdevices(config.meraki_api, nw, suppressprint=True)
        if devicelist != None:
            logger.info('Device List Has Been Retrieved')
            for devices in devicelist:
                deviceSerialList.append(devices['serial'])
            return deviceSerialList
        else:
            logger.info('No Device in the Network')
            return None
    except Exception as err:
        logger.error("ERROR in Retrieving Devices", exc_info=True)
        return ("ERROR in Retrieving Devices" + str(err))

def getClients(sns_ip_list,seriallist): #seriallist IS getDevices Function
    clientmaclist=[]
    try:
        logger.info('Search for the Client MAC with Appropriate IP Address has been started, (iterate through devices in the order of MR,MS and MX) => This can be added')
        for client_ip in sns_ip_list:
            for serial in seriallist:
                connected_endpoints = meraki.getclients(config.meraki_api, serial, timestamp=86400, suppressprint=True)
                logger.info('Clients have been gathered for %(serial)s ', {'serial' : serial})
                for endpoint in connected_endpoints:
                    if endpoint['ip'] == client_ip:
                        logger.info('Device is found connected to %(serial)s MAC Value %(endpoint_mac)s will be added to list', {'serial':serial, 'endpoint_mac':endpoint['mac']})
                        clientmaclist.append(endpoint['mac'])
        return clientmaclist
    except Exception as err:
        logger.error("ERROR in Retrieving Clients", exc_info=True)
        return ("ERROR in Retrieving Clients" + str(err))


def remediateClient(clientmaclist,nw): #clientmac is getClients  and nw is getNetwork
    try:
        for clientmac in clientmaclist:
            logger.info('Remediation Started for %(clientmac)s', {'clientmac':clientmac})
            result=meraki.updateclientpolicy(config.meraki_api, nw, clientmac, 'blocked', policyid=None,suppressprint=True)
            if result['type'] == 'blocked':
                logger.info("Remediation successful for %(client_mac)s ", {'client_mac':client_mac})
        logger.info("Remediation Finished", exc_info = True)
    except Exception as err:
        logger.error("ERROR in Remediating the Misbehaviouring Client", exc_info=True)
        return ("ERROR in Retrieving Clients" + str(err))

def lambda_handler(event, context):
    alerting_ip_list=[]
    message = event['Records'][0]['Sns']['Message']
    #print(message)
    message_json=json.loads(message)  #TO DESERIALIZE THE SNS JSON STRING TO
    try:
        org = getOrg()
        nw = getNetwork(org)
        devices=getDevices(nw)

        for alerting_ip in message_json["source_info"]["ips"]:
            alerting_ip_list.append(alerting_ip)
            logger.info("Able to Parse the Alerting IP Address  %(alerting_ip)s",{'alerting_ip':alerting_ip} )

        client_mac_list = getClients(alerting_ip_list, devices)
        remediateClient(client_mac_list,nw)
    except Exception as err:
        logger.error("ERROR in Lambda", exc_info=True)
        return ("ERROR in Lambda" + str(err))


"""TRYING TO ACHIEVE AUTO REMEDIATION SCENARIO WITH MERAKI CLOUD AND STEALTHWATCH CLOUD VIA AWS LAMBDA SNS AS TRIGGER

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
