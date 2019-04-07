from time import sleep
import requests

BASE_URL = "https://api.groupme.com/v3"
TOKEN = "paste your developer access token here"

print("GroupMe test application demonstrating REST API.\n")

#make group
print("Making group.")
GROUP_NAME = "GL Cisco"
group_id = None
params = {"token": TOKEN}
payload = {"name": GROUP_NAME} 
headers = {"content-type": "application/json"}
end_point = "/groups"
url = "%s%s" % (BASE_URL, end_point)
r = requests.post(url, headers=headers, params=params, json=payload)
if r.status_code != 201:
    raise Exception("Bad request. Unable to create group. " + r.text)
else:
    group = r.json()["response"]
    group_id = group["id"]

#add member
print("Adding member.")
MEMBER_NAME = "NetAcad1"
member_id = None
phone_number = input("Please enter your mobile number: ")
params = {"token": TOKEN}
payload = {"members": [{"nickname": MEMBER_NAME, "phone_number": phone_number}]} 
headers = {"content-type": "application/json"}
end_point = "/groups/%s/members/add" % group_id
url = "%s%s" % (BASE_URL, end_point)
r = requests.post(url, headers=headers, params=params, json=payload)
if r.status_code != 202:
    raise Exception("Bad request. Unable to create member request. " + r.text)
else:
    member_id = r.json()["response"]["results_id"]

#add bot
print("Creating bot.")
bot_id = None
params = {"token": TOKEN}
payload = {"bot": {"name": "ghBot", "group_id": group_id}} 
headers = {"content-type": "application/json"}
end_point = "/bots"
url = "%s%s" % (BASE_URL, end_point)
r = requests.post(url, headers=headers, params=params, json=payload)
if r.status_code != 201:
    raise Exception("Bad request. Unable to create bot. " + r.text)
else:
    bot = r.json()["response"]["bot"]
    bot_id = bot["bot_id"]

#send message
print("Sending message.")
message = input("What message would you like to send: ")
params = {"token": TOKEN}
payload = {"bot_id": bot_id, "text": message}
headers = {"content-type": "application/json"}
end_point = "/bots/post"
url = "%s%s" % (BASE_URL, end_point)
r = requests.post(url, json=payload, headers=headers, params=params)
if r.status_code != 202:
    raise Exception("Unable to post message. " + r.text)

input("Press Enter to delete the GroupMe group and quit.")
#delete group
params = {"token": TOKEN}
headers = {"content-type": "application/json"}
end_point = "/groups/%s/destroy" % group_id
url = "%s%s" % (BASE_URL, end_point)
r = requests.post(url, headers=headers, params=params)
if r.status_code != 200:
    raise Exception("Bad request. Unable to remove group. Please verify your access token." + r.text)

print("GroupMe group is deleted. App is closing.")