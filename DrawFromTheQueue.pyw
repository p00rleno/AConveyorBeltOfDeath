import pprint
import random
import ctypes
import logging
import math
import os
import json
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
from twitchAPI.types import CustomRewardRedemptionStatus
from twitchAPI.types import SortOrder
from twitchAPI.types import TwitchAuthorizationException
from datetime import datetime
from os.path import exists

#globals
username = 'p00rleno'
appid = ''
apppwd = '' 
webserver_port = 17563
purge_all_entries = True
tickets_per_day = 1 #Set to how many tickets someone should get per day. Note that all integer values have the same behavior, since everyone grows at the same rate
                    #If you want interesting behaviors,set to a fraction e.g. 1/7 will increase your odds once per week
                    #0 means that everyone only gets 1 ticket per entry, that never grows
reward_cost = 5000
reward_description = 'Join the queue to eventually have a Rimworld colonist named after you. (Queue is reset every month and points refunded!)'
update_frequency = 60 # seconds, minimum refresh interval for queue
 

entries = []
last_update = datetime(2000, 1, 1)
twitch = []
reward_id_1 = ''
reward_name_1 = ''
reward_weight_1 = 1
reward_id_2 = ''
reward_name_2 = ''
reward_enable_2 = False
reward_weight_2 = 3
reward_id_3 = ''
reward_name_3 = ''
reward_enable_3 = False
reward_weight_3 = 5
max_entry_age = 0
purge_old_entries = False

viewer_list = []
use_viewer_list = False
viewers_only = False
viewer_preferance_factor = 1.0

used_viewer_list = []
block_duplicates = True
###Begin script###

def get_redemption_list(twitch, reward_id_1, reward_id_2, reward_id_3):
    global last_update
    global entries
    global user_id
    
    page = None
    now = datetime.utcnow()
    
    #Use the old list if it's not stale
    last_update_age = (now - last_update).total_seconds()
    logging.info('get_redemption_list: last_update_age: ' + str(last_update_age) )
    if last_update_age < update_frequency:
        return entries
    
    #Otherwise, go get them from the API
    
    last_update = now
    entries = []
    # loop over all redemptions, 50 at a time
    while True:
        redemptions = twitch.get_custom_reward_redemption(user_id, reward_id_1, None,CustomRewardRedemptionStatus.UNFULFILLED,SortOrder.OLDEST, page, 50)
        logging.info('get_redemption_list: got a page, length : ' +  str(len(redemptions['data'])))
        if len(redemptions['data']) == 0:
            break;
        # update cursor
        page = redemptions['pagination']['cursor']
        # build redemption list
        for redemption in redemptions['data']:
            # Calculate entry age
            date = datetime.strptime(redemption['redeemed_at'], '%Y-%m-%dT%XZ')
            age = now - date;
            entries.append({'name': redemption['user_name'], 'id': redemption['id'], 'age':age, 'rewardid': reward_id_1, 'weight': reward_weight_1})
            logging.info('get_redemption_list: entries.append: ' +  str(entries[-1]))
            
    
    #Repeat for redemptions 2 and 3
    page = None
    while reward_enable_2:
        redemptions = twitch.get_custom_reward_redemption(user_id, reward_id_2, None,CustomRewardRedemptionStatus.UNFULFILLED,SortOrder.OLDEST, page, 50)
        logging.info('get_redemption_list (reward2): got a page, length : ' +  str(len(redemptions['data'])))
        if len(redemptions['data']) == 0:
            break;
        # update cursor
        page = redemptions['pagination']['cursor']
        # build redemption list
        for redemption in redemptions['data']:
            # Calculate entry age
            date = datetime.strptime(redemption['redeemed_at'], '%Y-%m-%dT%XZ')
            age = now - date;
            entries.append({'name': redemption['user_name'], 'id': redemption['id'], 'age':age, 'rewardid': reward_id_2, 'weight': reward_weight_2})
            logging.info('get_redemption_list: entries.append: ' +  str(entries[-1]))
            
    page = None
    while reward_enable_3:
        redemptions = twitch.get_custom_reward_redemption(user_id, reward_id_3, None,CustomRewardRedemptionStatus.UNFULFILLED,SortOrder.OLDEST, page, 50)
        logging.info('get_redemption_list (reward3): got a page, length : ' +  str(len(redemptions['data'])))
        if len(redemptions['data']) == 0:
            break;
        # update cursor
        page = redemptions['pagination']['cursor']
        # build redemption list
        for redemption in redemptions['data']:
            # Calculate entry age
            date = datetime.strptime(redemption['redeemed_at'], '%Y-%m-%dT%XZ')
            age = now - date;
            entries.append({'name': redemption['user_name'], 'id': redemption['id'], 'age':age, 'rewardid': reward_id_3, 'weight': reward_weight_3})
            logging.info('get_redemption_list: entries.append: ' +  str(entries[-1]))
    
    
    return entries

def fulfill_entries(entries, rewardid):
    # Discard duplicates
    entries = list(set(entries))

    # Fulfill all, 50 at a time. That's all Twitch allows.
    num_fulfilled = 0
    while num_fulfilled < len(entries):
        new_fulfills = min(50, len(entries))
        twitch.update_redemption_status(user_id, rewardid, entries[num_fulfilled:num_fulfilled+new_fulfills], CustomRewardRedemptionStatus.FULFILLED)
        num_fulfilled += new_fulfills;
        
    return num_fulfilled
    
    
def reject_entries(entries,rewardid):
    # Discard duplicates
    entries = list(set(entries))

    # Fulfill all, 50 at a time. That's all Twitch allows.
    num_rejected = 0
    while num_rejected < len(entries):
        new_rejects = min(50, len(entries))
        twitch.update_redemption_status(user_id, rewardid, entries[num_rejected:num_rejected+new_rejects], CustomRewardRedemptionStatus.CANCELED)
        num_rejected += new_rejects;
        
    return num_rejected

def prune_old_entries(entries):
    if not purge_old_entries:
        return entries
    old_entries_1 = [element['id'] for element in entries if ((element['age'].days >= max_entry_age) and element['rewardid'] == reward_id_1)]
    old_entries_2 = [element['id'] for element in entries if ((element['age'].days >= max_entry_age) and element['rewardid'] == reward_id_2)]
    old_entries_3 = [element['id'] for element in entries if ((element['age'].days >= max_entry_age) and element['rewardid'] == reward_id_3)]
    num_old_entries = len(old_entries_1) + len(old_entries_2) + len(old_entries_3)
    if num_old_entries == 0:
        return entries
    reject_entries(old_entries_1, reward_id_1)
    reject_entries(old_entries_2, reward_id_2)
    reject_entries(old_entries_3, reward_id_3)
    return [element for element in entries if element['age'].days < max_entry_age]

def draw_one_entry(entries, tickets_per_day, purge_all):
    global use_viewer_list
    global viewers_only
    global viewer_preferance_factor
    global viewer_list
    
    tickets = []
    # Add tickets for each day old the entry is
    
    if use_viewer_list:
        #Force viewers to be drawn
        if viewers_only:
            for entry in entries:
                if entry['name'] in viewer_list:
                    age = entry['age']
                    weight = entry['weight']
                    for i in range(0,weight*(1+math.ceil(age.days * tickets_per_day))):
                        tickets.append(entry)
        #Weight viewer entries by a constant multiple
        else:
            for entry in entries:
                age = entry['age']
                weight = entry['weight']
                num_tickets_for_user = weight * (1+math.ceil(age.days * tickets_per_day))
                if entry['name'] in viewer_list: 
                    num_tickets_for_user *= viewer_preference_factor
                    num_tickets_for_user = round(num_tickets_for_user)
                for i in range(0,num_tickets_for_user):
                    tickets.append(entry)
    else:
        #Normal operation, everyone has a fair chance
        for entry in entries:
            age = entry['age']
            weight = entry['weight']
            #Ticket count = weight of redemption (for multiple-ticket redemptions) * (1+ticket growth factor * ticket age)
            for i in range(0,weight*(1+math.ceil(age.days * tickets_per_day))):
                tickets.append(entry)
            
    #Count tickets generated
    num_tickets = len(tickets)
    logging.info('draw_one_entry: num_tickets: ' +  str(num_tickets))
    if num_tickets == 0:
        return {'name': 'Chat is Cowards (Nobody entered)', 'total_entries': '0', 'winning_entries': '0', 'total_tickets': '0', 'winners_tickets': '0'}
    
    # Load old used viewers
    usedNameFile = os.path.join(os.path.dirname(__file__), "used_viewers.ini")
    used_viewer_list = []
    if exists(usedNameFile) and block_duplicates:
        with open(usedNameFile,'r') as fin:
            lines = fin.readlines()
            for line in lines:
                used_viewer_list.append(line.strip())
    
    # Pick a winner
    numTries = 0
    maxTries = 100000
    while numTries < maxTries:
        winning_ticket_number = random.randint(0,num_tickets-1)
        winning_ticket = tickets[winning_ticket_number]
        logging.info('draw_one_entry: winning_ticket_number: ' +  str(winning_ticket_number))
        logging.info('draw_one_entry: winning_ticket: ' +  str(winning_ticket))
        # Keep the winner if it's new, or we don't care about duplicates
        if (not any(s.lower() == winning_ticket['name'].lower() for s in used_viewer_list)) or not block_duplicates:
            break
        numTries += 1
        if numTries == maxTries:
            return {'name': 'Chat is Cowards (Too many duplicate names)', 'total_entries': '0', 'winning_entries': '0', 'total_tickets': '0', 'winners_tickets': '0'}
            
    used_viewer_list.append(winning_ticket['name'])
    
    # Save used viewer list
    if block_duplicates:
        file=open(usedNameFile,'w')
        for name in used_viewer_list:
            file.writelines(name + '\r')
        file.close()
    
    # Figure out which redemptions to fulfill, and fulfill them
    entries_to_fulfill = []
    if purge_all:
        entries_to_fulfill = [element for element in entries if element['name'] == winning_ticket['name']]
    else:
        entries_to_fulfill = [winning_ticket]
        
    #Assign by which redemption they took
    IDs_to_fulfill_1 = [entry['id'] for entry in entries_to_fulfill if entry['rewardid'] == reward_id_1]
    IDs_to_fulfill_2 = [entry['id'] for entry in entries_to_fulfill if entry['rewardid'] == reward_id_2]
    IDs_to_fulfill_3 = [entry['id'] for entry in entries_to_fulfill if entry['rewardid'] == reward_id_3]
    
    logging.info('draw_one_entry: IDs_to_fulfill: ' +  str(len(IDs_to_fulfill_1)+ len(IDs_to_fulfill_2) + len(IDs_to_fulfill_3)) + ' items')
    
    #Fulfill them
    num_fulfilled = 0
    if (len(IDs_to_fulfill_1) > 0):
        num_fulfilled += fulfill_entries(IDs_to_fulfill_1, reward_id_1)
    if (len(IDs_to_fulfill_2) > 0):
        num_fulfilled += fulfill_entries(IDs_to_fulfill_2, reward_id_2)
    if (len(IDs_to_fulfill_3) > 0):
        num_fulfilled += fulfill_entries(IDs_to_fulfill_3, reward_id_3)
    logging.info('draw_one_entry: num_fulfilled: ' +  str(num_fulfilled))
    
    num_winners_entries = len(IDs_to_fulfill_1) * reward_weight_1 + len(IDs_to_fulfill_2) * reward_weight_2 + len(IDs_to_fulfill_3) * reward_weight_3
    
    # Count user tickets, for funsies
    all_winners_tickets = [element for element in tickets if element['name'] == winning_ticket['name']]
    
    # Count num entrants, for funsies
    num_entrants = len(set([element['name'] for element in tickets if True]))
    
    return {'name': winning_ticket['name'], 'total_entries': len(entries), 'winning_entries': num_winners_entries, 'total_tickets': num_tickets, 'winners_tickets': len(all_winners_tickets), 'total_entrants': num_entrants}
    
def user_stats(entries, username, tickets_per_day):
    tickets = []
    # Calculate the tickets, as if doing a draw
    for entry in entries:
        age = entry['age']
        weight = entry['weight']
        for i in range(0,weight * (1+math.ceil(age.days * tickets_per_day))):
            tickets.append(entry)
    
    #Calculate how many entries of each type are in queue, and multiply by weight
    entries_1 = [element for element in entries if element['rewardid'] == reward_id_1]
    entries_2 = [element for element in entries if element['rewardid'] == reward_id_2]
    entries_3 = [element for element in entries if element['rewardid'] == reward_id_3]
    num_entries = len(entries_1) * reward_weight_1 + len(entries_2) * reward_weight_2 + len(entries_3) * reward_weight_3
    
    #Calculate how many entries the given user has, and multiply by weight
    user_entries = [element for element in entries if element['name'].upper() == username.upper()]
    user_entries_1 = [element for element in user_entries if element['rewardid'] == reward_id_1]
    user_entries_2 = [element for element in user_entries if element['rewardid'] == reward_id_2]
    user_entries_3 = [element for element in user_entries if element['rewardid'] == reward_id_3]
    num_user_entries = len(user_entries_1) * reward_weight_1 + len(user_entries_2) * reward_weight_2 + len(user_entries_3) * reward_weight_3
    
    #Calculate total number of tickets, and user's number of tickets
    num_tickets = len(tickets)
    user_tickets = [element for element in tickets if element['name'].upper() == username.upper()]
    num_user_tickets = len(user_tickets)
    
    #Calculate number of different usernames in the queue
    num_entrants = len(set([element['name'] for element in tickets if True]))
    
    return {'name': username, 'total_entries': num_entries, 'user_entries': num_user_entries, 'total_tickets': num_tickets, 'user_tickets': num_user_tickets, 'total_entrants': num_entrants}
    
def queue_stats(entries, tickets_per_day):
    #Queue stats is implemented as getting user stats for a random user (me! who would have thought)
    #Throwing away the user specific part, and returning the global stats
    dummy_user_stats = user_stats(entries, 'p00rleno', tickets_per_day)
    return {'total_entries': dummy_user_stats['total_entries'], 'total_tickets': dummy_user_stats['total_tickets'],  'total_entrants': dummy_user_stats['total_entrants']}

def update_active_viewers(viewerList):
    global viewer_list
    #Viewer list comes in as a : seperated list from StreamLabs
    viewer_list = viewerList.split(":")
    return len(viewer_list)
    
def process_message(message):
    global twitch
    global reward_id_1
    global reward_id_2
    global reward_id_3
    global purge_all_entries
    global tickets_per_day
    #Notably: NOT global entries 
    # In general, we get the entry list (from cache, or from API),
    # Then clean up expired entries, and then perform our action
    # and return it to the loop for printing to the py2 process
    logging.info('process_message: message: ' + message )
    if message == 'draw':
        entries = get_redemption_list(twitch, reward_id_1, reward_id_2, reward_id_3)
        entries = prune_old_entries(entries)
        return draw_one_entry(entries, tickets_per_day, purge_all_entries)
    elif message.startswith('userinfo'):
        entries = get_redemption_list(twitch, reward_id_1, reward_id_2, reward_id_3)
        entries = prune_old_entries(entries)
        return user_stats(entries, message.replace("userinfo", "", 1).strip(), tickets_per_day)
    elif message == 'queueinfo':
        entries = get_redemption_list(twitch, reward_id_1, reward_id_2, reward_id_3)
        entries = prune_old_entries(entries)
        return queue_stats(entries, tickets_per_day)
    elif message == 'loadsettings':
        load_settings()
        return {'OK':1 }
    elif message == 'viewerlist':
        count = update_active_viewers(message.replace("viewerlist","",1).strip())
        return {'OK':count }
    else:
        return '???'
        
def login_and_setup():
    global twitch
    global username
    global user_id
    global reward_id_1
    global reward_id_2
    global reward_id_3
    global reward_name_1
    global reward_weight_1
    global reward_name_2
    global reward_weight_2
    global reward_enable_2
    global reward_name_3
    global reward_weight_3
    global reward_enable_3
    global reward_cost
    global reward_description
    global webserver_port
    
    # create instance of twitch API and create app authentication
    twitch = Twitch(appid, apppwd)

    # get oauth scope for managing channel points
    target_scope = [AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS]
    try:
        auth = UserAuthenticator(twitch, target_scope, force_verify=True, url=('http://localhost:' + str(webserver_port)))
        auth.port = webserver_port
        # this will open your default browser and prompt you with the twitch verification website
        token, refresh_token = auth.authenticate()
    except:
        raise IOError("Port already in use!")

    # get ID of user we're logged in as
    user_info = twitch.get_users(logins=[username])
    user_id = user_info['data'][0]['id']
    
    logging.info('login_and_setup: user_id: ' + user_id )


    # add user authentication to object under appropriate scope
    twitch.set_user_authentication(token, target_scope, refresh_token)

    # get all channel point redemption options
    rewards = twitch.get_custom_reward(user_id)

    # find correct reward IDs
    # a bit inefficient as done here but meh
    reward_id_1 = ''
    for reward in rewards['data']:
        if reward_name_1 in reward['title']:
            reward_id_1 = reward['id']
            
    reward_id_2 = None
    if(reward_enable_2):
        reward_id_2 = ''
        for reward in rewards['data']:
            if reward_name_2 in reward['title']:
                reward_id_2 = reward['id']
                
    reward_id_3 = None
    if(reward_enable_3):
        reward_id_3 = ''
        for reward in rewards['data']:
            if reward_name_3 in reward['title']:
                reward_id_3 = reward['id']
        
            
    # create reward if it didn't already exist
    if reward_id_1 == '':
        reward = twitch.create_custom_reward(user_id, reward_name_1, reward_cost * reward_weight_1, reward_description, True, None, False, False, None, False, None, False, None, False)
        reward_id_1 = reward['data'][0]['id']
        logging.warning('Created new reward in your channel. Go to the Dashboard to customize it!')
    
    
    # create reward 2 if it didn't already exist
    if reward_id_2 == '':
        reward = twitch.create_custom_reward(user_id, reward_name_2, reward_cost * reward_weight_2, reward_description, True, None, False, False, None, False, None, False, None, False)
        reward_id_2 = reward['data'][0]['id']
        logging.warning('Created new reward in your channel. Go to the Dashboard to customize it!')
        
    # create reward 3 if it didn't already exist
    if reward_id_3 == '':
        reward = twitch.create_custom_reward(user_id, reward_name_3, reward_cost * reward_weight_3, reward_description, True, None, False, False, None, False, None, False, None, False)
        reward_id_3 = reward['data'][0]['id']
        logging.warning('Created new reward in your channel. Go to the Dashboard to customize it!')
        
    logging.info('login_and_setup: RewardID 1: ' + reward_id_1 )
    if reward_id_2 != None:
        logging.info('login_and_setup: RewardID 2: ' + reward_id_2 )
    if reward_id_3 != None:
        logging.info('login_and_setup: RewardID 3: ' + reward_id_3 )


def load_settings():
    global username
    global appid
    global apppwd
    global purge_all_entries
    global tickets_per_day
    global reward_name_1
    global reward_weight_1
    global reward_name_2
    global reward_weight_2
    global reward_enable_2
    global reward_name_3
    global reward_weight_3
    global reward_enable_3
    
    global update_frequency
    global max_entry_age
    global purge_old_entries
    global use_viewer_list
    global viewers_only
    global viewer_preferance_factor
    global webserver_port 
    global block_duplicates
    
    SettingsFile = os.path.join(os.path.dirname(__file__), "QueueBotSettings.json")
    
    f = open(SettingsFile)
    data = f.read()
    while data[0] != '{':
        data = data[1:len(data)]
    ScriptSettings = json.loads(data)
    f.close()
    
    username = ScriptSettings['Username']
    appid = ScriptSettings['appID']
    apppwd = ScriptSettings['appSecret']
    purge_all_entries = ScriptSettings['PurgeAll']
    tickets_per_day = float(ScriptSettings['TicketsPerDay'])
    
    reward_name_1 = ScriptSettings['RewardName']
    reward_weight_1 = ScriptSettings['RewardValue1']
    
    reward_name_2 = ScriptSettings['RewardName2']
    reward_weight_2 = ScriptSettings['RewardValue2']
    reward_enable_2 = ScriptSettings['RewardEnable2']
    
    reward_name_3 = ScriptSettings['RewardName3']
    reward_weight_3 = ScriptSettings['RewardValue3']
    reward_enable_3 = ScriptSettings['RewardEnable3']

    update_frequency = ScriptSettings['APIFrequency']
    purge_old_entries = ScriptSettings['PurgeOld']
    max_entry_age = ScriptSettings['OldAgeLimit']
    
    use_viewer_list = ScriptSettings['UseViewerList']
    viewers_only = ScriptSettings['DrawViewersOnly']
    viewer_preference_factor = float(ScriptSettings['ViewerAdvantageFactor'])
    
    block_duplicates = ScriptSettings['BlockDuplicates']
    
    serverAddress = ScriptSettings['webserverPort']
    try:
        webserver_port = int(serverAddress.split(':')[-1])
    except:
        webserver_port = 80
    


def main():
    #logging.basicConfig(filename='c:\debug.log', encoding='utf-8',level=logging.INFO)
    try:
        load_settings()
    except:
        print('BADSETTING')
        return 
    try:
        login_and_setup()
    except IOError:
        print('NOBIND')
        return
    except TwitchAuthorizationException:
        print('NOTWITCH')
        return
    except:
        print('ERRUNK')
        return
        
    print('ready')
    while(True):
        logging.info('__main__: waiting' )
        message = input().strip()
        if(message.lower().startswith('quit')):
            logging.info('__main__: quit' )
            exit
            break
        result = process_message(message)
        print(result)
    return

if __name__ == "__main__":
    main()
