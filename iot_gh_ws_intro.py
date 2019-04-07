from time import sleep
from iot_gh.IoTGreenhouseService import IoTGreenhouseService
from iot_gh.GHTextingService import GHTextingService

TOKEN = "your token here"
last_id = None

ghs = IoTGreenhouseService()
ts = GHTextingService(TOKEN, ghs)

while True:
    lm = ts.last_message
    if lm.id != last_id:
        print(lm.name + "   " + lm.text)
        print()

        last_id = lm.id
    sleep(.5)
    # Author: Keith E. Kelly - 1/12/2019
import threading
import requests
import time
from SMSCommands import SMSCommands

from ghs_mock import ghs_mock as MockIoTGreenhouseService

class SMSTextMessage(object):
    id = None
    name = None
    text = None
    commands = None

class SMSGroupMember(object):
    id = None
    name = None
    phone_number = None
    result_id = None

    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number

class SMSGroupMeService(threading.Thread):
    
    BASE_URL = "https://api.groupme.com/v3"
    
    _gh = None
    _access_token = ""
    _group_id = ""
    _bot_id = ""
    _last_scanned_message_id = None
    
    scanning = False
    bot_name = ""
    commands = None
    members = None
    last_message = None
    command_list = None
 
    def __init__(self, access_token, testing=False):
        threading.Thread.__init__(self)
        
        if testing:
            self.ghs = MockIoTGreenhouseService()
        else:
            from iot_gh.IoTGreenhouseService import IoTGreenhouseService
            self.ghs = IoTGreenhouseService()
        self._access_token = access_token
        
        self._group_name = "%s_%s_%s" % ("iot_gh", self.ghs.greenhouse.group_id, self.ghs.greenhouse.house_number )
        self.bot_name = "%s%s" % ("gh",self.ghs.greenhouse.house_number)
        
        self.commands = SMSCommands()
        self.members = []

        self._group_id = self._get_group_id()
        if self._group_id == None:
            self._group_id = self._make_group()
        self._bot_id = self._get_bot_id()
        if self._bot_id == None:
            self._bot_id = self._make_bot()
        self._delete_sms_mode()
        #self._send_intro_message()
        #self._last_scanned_message_id = self._get_last_scanned_message_id()
        
        self.daemon = True
        #self.start()

    def run(self):
        self.scanning = True
        self._send_message("%s is on-line." % self.bot_name)
        while self.scanning:
            next_commands = self._get_next_commands()
            if next_commands != None:
                self._execute_commands(next_commands)
            time.sleep(5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def close(self):
        self._send_message("Removing group and members")
        time.sleep(1)
        self._delete_group()
        
    def _delete_group(self):
        params = {"token": self._access_token}
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/destroy" % self._group_id
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.post(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to remove group. Please verify your access token." + r.text)

       
    def _get_group_id(self):
        group_id = None
        params = {"token": self._access_token}
        headers = {"content-type": "application/json"}
        end_point = "/groups"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch group. Please verify your access token." + r.text)
        else:
            groups = r.json()["response"]
            for group in groups:
                if group["name"] == self._group_name:
                    group_id = group["id"]
                    group_phone_number = group["phone_number"]
                    break
        return group_id
    
    def _make_group(self):
        group_id = None
        params = {"token": self._access_token}
        payload = {"name": self._group_name} 
        headers = {"content-type": "application/json"}
        end_point = "/groups"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.post(url, headers=headers, params=params, json=payload)
        if r.status_code != 201:
            raise Exception("Bad request. Unable to create group. " + r.text)
        else:
            group = r.json()["response"]
            group_id = group["id"]
        return group_id

    def _get_bot_id(self):
        bot_id = None
        #payload = {"group_id": self._group_id}
        headers = {"content-type": "application/json"}
        end_point = "bots"
        url = "%s/%s?token=%s" % (self.BASE_URL, end_point, self._access_token)
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        else:
            bots = r.json()["response"]
            for bot in bots:
                if bot["name"] == self.bot_name and bot["group_id"] == self._group_id:
                    bot_id = bot["bot_id"]
                    break
        return bot_id

    def _make_bot(self):
        bot_id = None
        payload = {"bot": {"name": self.bot_name, "group_id": self._group_id}} 
        headers = {"content-type": "application/json"}
        #url = self.BASE_URL + "/bots?token=" + self._access_token
        end_point = "bots"
        url = "%s/%s?token=%s" % (self.BASE_URL, end_point, self._access_token)
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code != 201:
            raise Exception("Bad request. Unable to create bot. " + r.text)
        else:
            bot = r.json()["response"]["bot"]
            bot_id = bot["bot_id"]
        return bot_id

    def _delete_sms_mode(self):
        params = {"token": self._access_token}
        params["limit"] = 1 
        headers = {"content-type": "application/json"}
        end_point = "/users/sms_mode/delete"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.post(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to disable SMS mode. " + r.text)
       
    def _get_member_id(self, response_id):
        params = {"token": self._access_token}
        params["limit"] = 1 
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/members/results/%s" % (self._group_id, response_id)
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        else:
            members = r.json()["response"]
            #should be only one
            member_id = members["members"][0]["id"]
                   
        return member_id
    
    def _remove_member(self, member_id):
        params = {"token": self._access_token}
        params["limit"] = 1 
        headers = {"content-type": "application/json"}
        end_point = "groups/%s/members/%s/remove" % (self._group_id, member_id)
        url = "%s/%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        

    def add_member(self, phone_number):
        if phone_number not in self.members:
            user_name = "User%s-%d" % (self.ghs.greenhouse.house_number,len(self.members) + 1)
            member = SMSGroupMember(user_name, phone_number)
            params = {"token": self._access_token}
            params["limit"] = 1  
            payload = {"members": [{"nickname": member.name, "phone_number": member.phone_number, "guid": member.name}]} 
            headers = {"content-type": "application/json"}
            end_point = "/groups/%s/members/add" % self._group_id
            url = "%s%s" % (self.BASE_URL, end_point)
            r = requests.post(url, headers=headers, params=params, json=payload)
            if r.status_code != 202:
                raise Exception("Bad request. Unable to create member request. " + r.text)
            else:
                member.result_id = r.json()["response"]["results_id"]
                self.members.append(member)

    
    def _send_message(self, message):
        params = {"token": self._access_token}
        params["limit"] = 1 
        payload = {"bot_id": self._bot_id, "text": message}
        headers = {"content-type": "application/json"}
        end_point = "/bots/post"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.post(url, json=payload, headers=headers, params=params)
        if r.status_code != 202:
            raise Exception("Unable to post message. " + r.text)
        else:
            self.last_message = SMSTextMessage()
            self.last_message.id = str(time.time())
            self.last_message.name = "gh"
            self.last_message.text = message
        
    #def _send_intro_message(self):
    #    m = "Hello. Send me a direct message (@gh) with the text '#help' for a list of IoT Greenhouse text commands. Use '#help-verbose' for detailed help text."
    #    self._send_message(m)

    
    def _get_last_scanned_message_id(self):
        last_message_id = None
        params = {"token": self._access_token}
        params["limit"] = 1  
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/messages" % self._group_id
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Unable to fetch messages. " + r.text)
        else:
            messages= r.json()["response"]["messages"]
            if len(messages) > 0:
                last_message_id = messages[0]["id"]
            else:
                raise Exception("No last message fount. " + r.text)

        return last_message_id
    
    def _get_next_commands(self):
        commands = None
        params = {"token": self._access_token}
        params["after_id"] = self._last_scanned_message_id  
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/messages" % self._group_id
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Unable to fetch messages. " + r.text)
        else:
            messages= r.json()["response"]["messages"]
            count = len(messages)
            if count > 0:
                self._last_scanned_message_id = messages[count-1]["id"]
                for message in messages:
                    if not (message["system"] or message["sender_type"] == "bot"):
                        if message["name"].split("-")[0] == "User%s" % self.ghs.greenhouse.house_number:
                            values = message["text"].strip().split(" ")
                            if values[0][1:] == self.bot_name:
                                self._last_scanned_message_id = message["id"]
                                self.last_message = SMSTextMessage()
                                self.last_message.id = message["id"]
                                self.last_message.name = message["name"]
                                self.last_message.text = message["text"]
                                #dump bot name at start
                                commands = values[1:]
                                break
                            else:
                                time.sleep(1)
                                self._send_message("Sorry. I'd like to chat, but I'm only configured to response to valid IoT Greenhouse commands. Use '#help' to see a list of valid commands.")
                
        return commands

    def _execute_commands(self, commands):
        cmds = [command.lower() for command in commands]
        cmds = [command.strip() for command in commands]
        if self._valid_commands(cmds):
            for cmd in cmds:
                inner = self.commands[cmd]
                if inner.result != None:
                    self._send_message(inner.result)
                
                if  inner.gh_function != None:
                    try:
                        this_function = "self.%s" % inner.gh_function
                        exec(this_function)
                    except:
                        self._send_message("Error: Invalid IoT Greenhouse command defined in command configuration file. %s" % inner.gh_function)
 
    def _valid_commands(self, commands):
        valid = True
        
        for command in commands:
            if command not in self.commands:
                self._send_message("Sorry. I'd like to chat, but I'm only configured to response to valid IoT Greenhouse commands. Use '#help' or '#help_verbose' to see a list of valid commands.")
                valid = False                
                break
        return valid

    def _load_command_file(self, filename):
        """Reads commands from CSV file
        """
        try:
            with open(filename) as csvfile:
                cmd_reader = csv.reader(csvfile, delimiter=',')
                self.command_list = {}
                for cmd in cmd_reader:
                    self.command_list[cmd[0]] = [cmd[1], cmd[2], cmd[3]] 

        except Exception as e:
            raise Exception("Unable to load commands. %s" % str(e))

    def stop_SMS_service(self):
        self.scanning = False
        #m = "Service stopped."
        #self._send_message(m)
    
    def send_command_list(self):
         m = "Valid IoT Greenhouse commands are: %s" % " ".join(self.commands.keys() )
         self._send_message(m)

    def send_command_details(self):
        str_list = []
        str_list.append("Valid IoT Greenhouse commands are:\n\n")
        for cmd in self.command_list:
            s = "%s  %s\n" % (cmd, self.command_list[cmd][1])
            str_list.append(s)
  
        m =  "".join(str_list)
        self._send_message(m)

    def send_temperature(self):   
        temp = self.ghs.temperature.get_inside_temp_F()
        m = "Current greenhouse temperature is %s." % temp
        self._send_message(m)         

#if __name__ == "__main__":
    
    




