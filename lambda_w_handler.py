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
    nwlist=[]
    try:
        logger.info('Organzations added to OrgList moving to Network List')
        for orgs in orglist:
            print(orgs)
            nws = meraki.getnetworklist(config.meraki_api, orgs, templateid=None, suppressprint=True) #THAT LINE NEEDS TO BE CHANGED, NOW IT IS STATIC FOR ONE ORGANIZATION
            if nws != None:
                for nwid in nws:
                    print(nwid['id'])
                    nwlist.append(nwid['id'])
                    logger.info('Network List Has been Retrieved')
        if len(nwlist) != 0:
            return nwlist
        else:
            logger.error('Network List is Empty')
    except Exception as err:
        logger.error("ERROR in Getting Network", exc_info=True)
        return ("ERROR in Getting Network" + str(err))

def getDevices(nwlist):
    deviceSerialList=[]
    try:
        logger.info('Searching for Devices Initated')
        for nw in nwlist:
            devicelist = meraki.getnetworkdevices(config.meraki_api, nw, suppressprint=True)
            logger.info('Device List Has Been Retrieved for %(nw)s ', {'nw':nw})
            for devices in devicelist:
                deviceSerialDict = {}
                deviceSerialDict['serial'] = devices['serial']
                deviceSerialDict['networkId'] = devices['networkId']
                deviceSerialList.append(deviceSerialDict)
        if len(deviceSerialList) != 0:
            return deviceSerialList
        else:
            logger.error('No Device in the Network')
            return None
    except Exception as err:
        logger.error("ERROR in Retrieving Devices", exc_info=True)
        return ("ERROR in Retrieving Devices" + str(err))

def getClients(sns_ip_list,seriallist): #seriallist IS getDevices Function
    endpoint_pair_list=[]
    try:
        logger.info('Search for the Client MAC with Appropriate IP Address has been started, (iterate through devices in the order of MR,MS and MX) => This can be added')
        for client_ip in sns_ip_list:
            for serial in seriallist:
                connected_endpoints = meraki.getclients(config.meraki_api, serial['serial'], timestamp=86400,
                                                        suppressprint=True)
                logger.info('Clients have been gathered for %(serial)s ', {'serial': serial['serial']})
                for endpoint in connected_endpoints:
                    if endpoint['ip'] == client_ip:
                        logger.info('Device is found connected to %(serial)s MAC Value will be returned',
                                    {'serial': serial['serial']})
                        endpoint_pair = dict()
                        endpoint_pair['mac'] = endpoint['mac']
                        endpoint_pair['networkId'] = serial['networkId']
                        endpoint_pair_list.append(endpoint_pair)
            if len(endpoint_pair_list) == 0:
                logger.info('Client has not been found for %(serial)s ', {'serial': serial['serial']})
                return None
            else:
                return endpoint_pair_list
    except Exception as err:
        logger.error("ERROR in Retrieving Clients", exc_info=True)
        return ("ERROR in Retrieving Clients" + str(err))


def remediateClient(ep_pair_list): #ep_pair list
    try:
        for ep_pair in ep_pair_list:
            logger.info('Remediation Started for %(clientmac)s', {'clientmac':ep_pair['mac']})
            result=meraki.updateclientpolicy(config.meraki_api, ep_pair['networkId'], ep_pair['mac'], 'blocked', policyid=None,suppressprint=True)
            if result['type'] == 'blocked':
                logger.info("Remediation successful for %(client_mac)s ", {'client_mac':ep_pair['mac']})
        logger.info("Remediation Finished", exc_info = True)
    except Exception as err:
        logger.error("ERROR in Remediating the Misbehaviouring Client", exc_info=True)
        return ("ERROR in Retrieving Clients" + str(err))

def lambda_handler(event, context):
    alerting_ip_list=[]
    message = event['Records'][0]['Sns']['Message']
    message_json=json.loads(message)  #TO DESERIALIZE THE SNS JSON STRING TO
    try:
        org = getOrg()
        nw = getNetwork(org)
        devices=getDevices(nw)

        for alerting_ip in message_json["source_info"]["ips"]:
            alerting_ip_list.append(alerting_ip)
            logger.info("Able to Parse the Alerting IP Address  %(alerting_ip)s",{'alerting_ip':alerting_ip} )

        ep_pair_list = getClients(alerting_ip_list, devices)
        remediateClient(ep_pair_list)
    except Exception as err:
        logger.error("ERROR in Lambda", exc_info=True)
        return ("ERROR in Lambda" + str(err))

