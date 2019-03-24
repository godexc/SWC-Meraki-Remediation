import config
import requests
import json
from meraki import meraki


print(meraki.myorgaccess(config.meraki_api,suppressprint=False))



"""TRYING TO ACHIEVE AUTO REMEDIATION SCENARIO WITH MERAKI CLOUD AND STEALTHWATCH CLOUD VIA AWS LAMBDA SNS AS TRIGGER

SCENARIO 1: CATCH and BLOCK INTERNAL IP SCANNER
SCENARIO 2: CATCH and BLOCK IPs CONNECTING TO BLACKLIST COUNTRIES

DOs : LOGGER, TRY/EXPECT and ERROR MANAGEMENT

NEEDS:
-NO API ON MERAKI SIDE THAT WILL RETURN THE MAC ADDRESS OF IP THEREFORE GOING TO USE S/N OF A DEVICE

-OVERALL FLOW
def getOrg()
GET/organizations => Retrieve return output[0]['id'] as organizationId

def getNetwork()
GET/organizations/{organizationId}/networks => Retrieve return output[0]['id'] as NetworkId

def getDevices()
GET/networks/[networkId]/devices => Search for output[i]['model'] startswith MX and based on that use the same i return output[i]['serial']

def getClients()
GET/devices/[serial]/clients?timespan=7200 => Search for the IP Address specified in Stealthwatch Alert (SNS) for output[i]['ip']
equals SWCIP then use the same i return output[i]['mac']

def remediateClient()
PUT/networks/[networkId]/clients/[mac]/policy?timespan=1800&devicePolicy=Blocked => Use the MAC that has been found on the previous stage
to set device policy as blocked

-AUTOMATED FLOW CAN BE FIRST USE GET/networks/[networkId]/devices as TO FIND ALL THE S/Ns then USE GET/devices/[serial]/clients RECURSIVELY
TO FIND APPROPRIATE MAC-IP BINDING


-OUTPUT OF SNS AS FOLLOWS:
From SNS: {
"assigned_to": null,
"assigned_to_username": null,
"comments": {
"comments": [
{
"comment": "Closed Due To Inactivity",
"time": "2019-02-05T07:00:18.669396+00:00",
"user": null
},
{
"comment": "Updated by 1 observations",
"time": "2019-01-05T08:29:11.371646+00:00",
"user": null
},
{
"comment": "Updated by 1 observations",
"time": "2019-01-04T15:18:58.586224+00:00",
"user": null
},
{
"comment": "Updated by 1 observations",
"time": "2019-01-03T19:16:04.726372+00:00",
"user": null
}
],
"count": 4,
"text": "4 comments"
},
"created": "2019-01-03T15:40:00Z",
"description": "This is a test alert of a service.",
"hostname": "",
"id": 69,
"ips_when_created": [
"192.168.101.13"
],
"last_modified": "2019-01-05T08:29:11.342857Z",
"merit": 6,
"natural_time": "1\u00a0month, 2\u00a0weeks ago",
"new_comment": null,
"obj_created": "2019-01-03T16:15:43.732118Z",
"observations": [
27447,
29911,
29528,
28502
],
"priority": 20,
"publish_time": "2019-01-03T16:15:43.686570+00:00",
"resolved": true,
"resolved_time": "2019-02-05T07:00:18.666997Z",
"resolved_user": null,
"rules_matched": null,
"snooze_settings": null,
"source": 67,
"source_info": {
"created": "2018-09-21T15:00:25.559925+00:00",
"hostnames": [],
"ips": [
"192.168.101.13"
],
"name": "192.168.101.13",
"namespace": "default"
},
"source_name": "192.168.101.13",
"source_params": {
"id": 67,
"meta": "net-link",
"name": "192.168.101.13"
},
"tags": [],
"text": "Test Alert on 192.168.101.13\nhttps://cisco-hevyapan.obsrvbl.com/#/alerts/69",
"time": "2019-01-05T07:40:00Z",
"type": "Test Alert"
}