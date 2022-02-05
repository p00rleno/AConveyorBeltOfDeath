
import sys
sys.platform="win32"
from os.path import exists
import time
import json
import subprocess
import _subprocess
import os
from System.Collections.Generic import List
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "A Conveyor Belt Of Death"
Website = "https://www.p00rleno.com"
Description = "Channel point queue management script for AvE"
Creator = "p00rleno"
Version = "1.3.0.0"

global cmd
cmd = None
global ScriptSettings

def clear_used_name_list():
    #   Load settings
    NameFile = os.path.join(os.path.dirname(__file__), "used_viewers.ini")
    
    if exists(NameFile):
        os.remove(NameFile)

def process_draw():
    global cmd
    global ScriptSettings
    cmd.stdin.write('draw\r\n')
    cmd.stdin.flush()
    dataRaw = cmd.stdout.readline().strip().replace('\'','\"')
    dataOutput = json.loads(dataRaw)
    try:
        strMessage = ScriptSettings['ResponseDraw']
        strMessage = strMessage.format(name= ('@'+dataOutput['name']), t_tickets= dataOutput['total_tickets'], u_tickets= dataOutput['winners_tickets'], t_entries= dataOutput['total_entries'], u_entries= dataOutput['winning_entries'], t_usercount= dataOutput['total_entrants'])
        Parent.SendStreamMessage(strMessage)
    except:
        Parent.SendStreamMessage('@' + dataOutput['name'] + ' : Hold fast or expire, your time has come!')
    return
    
def process_queue(data):
    global cmd
    cmd.stdin.write('queueinfo\r\n')
    cmd.stdin.flush()
    dataRaw = cmd.stdout.readline().strip().replace('\'','\"')
    dataOutput = json.loads(dataRaw)
    try:
        strMessage = ScriptSettings['ResponseQueue']
        strMessage = strMessage.format(name= ('@'+data.UserName), t_tickets= dataOutput['total_tickets'], t_entries= dataOutput['total_entries'], t_usercount= dataOutput['total_entrants'])
        Parent.SendStreamMessage(strMessage)
    except:
        Parent.SendStreamMessage('@' + data.UserName + ' : There are currently ' + str(dataOutput['total_tickets']) + ' queue tickets from ' + str(dataOutput['total_entries']) + ' channel point redemptions')
    return
    
def process_user(data):
    global cmd
    cmd.stdin.write('userinfo ' + data.UserName + '\r\n')
    cmd.stdin.flush()
    dataRaw = cmd.stdout.readline().strip().replace('\'','\"')
    dataOutput = json.loads(dataRaw)
    multipleTickets = '' if dataOutput['user_tickets'] == 1 else 's'
    multipleEntries = '' if dataOutput['user_entries'] == 1 else 's'
    try:
        strMessage = ScriptSettings['ResponseUser']
        strMessage = strMessage.format(pluralTickets= multipleTickets, pluralEntries= multipleEntries, name= ('@'+dataOutput['name']), u_tickets= dataOutput['user_tickets'], t_tickets= dataOutput['total_tickets'], u_entries= dataOutput['user_entries'], t_entries= dataOutput['total_entries'], t_usercount= dataOutput['total_entrants'])
        Parent.SendStreamMessage(strMessage)
    except:
        Parent.SendStreamMessage('@' + data.UserName + ' : You currently have ' + str(dataOutput['user_tickets']) + ' active queue ticket' + multipleTickets + ' from ' + str(dataOutput['user_entries']) + ' channel point redemption' + multipleEntries)
    return
    
def process_user_other(data):
    global cmd
    cmd.stdin.write('userinfo ' + data.GetParam(1) + '\r\n')
    cmd.stdin.flush()
    dataRaw = cmd.stdout.readline().strip().replace('\'','\"')
    dataOutput = json.loads(dataRaw)
    multipleTickets = '' if dataOutput['user_tickets'] == 1 else 's'
    multipleEntries = '' if dataOutput['user_entries'] == 1 else 's'
    try:
        strMessage = ScriptSettings['ResponseUserOther']
        strMessage = strMessage.format(senderName= data.UserName, pluralTickets= multipleTickets, pluralEntries= multipleEntries, name= ('@'+dataOutput['name']), u_tickets= dataOutput['user_tickets'], t_tickets= dataOutput['total_tickets'], u_entries= dataOutput['user_entries'], t_entries= dataOutput['total_entries'], t_usercount= dataOutput['total_entrants'])
        Parent.SendStreamMessage(strMessage)
    except:
        Parent.SendStreamMessage('@' + data.UserName + ' : ' + data.GetParam(1) + ' currently has ' + str(dataOutput['user_tickets']) + ' active queue ticket' + multipleTickets + ' from ' + str(dataOutput['user_entries']) + ' channel point redemption' + multipleEntries)
    return
    
def update_user_list():
    global cmd
    viewerIDs = Parent.GetViewerList()
    viewers = Parent.GetDisplayNames(viewerIDs)
    viewerNames = viewers.values()
    viewerNameString = ':'.join(viewerNames)
    
    cmd.stdin.write('viewerlist ' + viewerNameString + '\r\n')
    cmd.stdin.flush()
    dataRaw = cmd.stdout.readline().strip().replace('\'','\"')
    Parent.Log(ScriptName,'Updated viewer list with ' + dataRaw + ' viewers')

def stary_py3_subprocess():
    global cmd
    global ScriptSettings
    cmdline = [ScriptSettings['Python3Path'] + 'python', os.path.join(os.path.dirname(__file__), "DrawFromTheQueue.pyw")]
    startupinfo = subprocess.STARTUPINFO()
    readyString = ''
    
    
    if not exists(os.path.expandvars(ScriptSettings['Python3Path'] + 'python.exe')):
        raise IOError("Failed to run python -- is your Python3 path correct?")
    try:
        cmd = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo, shell=True)
        time.sleep(5)
        readyString = cmd.stdout.readline().strip()
    except OSError:
        raise IOError("Failed to start Python3. Ensure your Python 3 path is set correctly to the location of python.exe in script settings.")
    else:
        if(readyString == 'NOBIND'):
            raise Exception("Couldn't start Authentication server to get Twitch auth token. Is the script already running?")
        if(readyString == 'NOTWITCH'):
            raise Exception("Couldn't authenticate app with Twitch Dev API -- are your app ID and secret set correctly?")
        if(readyString == 'BADSETTTING'):
            raise Exception("A script setting could not be processed. Check that all your settings make sense.")
        if(readyString == 'ERRUNK'):
            raise Exception("Py3 script encountered an unknown error initializing the Twitch API. Bug p00rleno or debug it in Idle")
        if(cmd.poll() != None):
            raise Exception("Python3 crashed. Its crash text started with " + readyString + " -- If this doesn't make the problem obvious, run the py3 script standalone and look at the output.")
    return

def perform_py3_setup():
    global cmd
    global ScriptSettings
    cmdline = [os.path.expandvars(ScriptSettings['Python3Path'] + 'scripts\\pip3.exe'), "install","twitchapi"]
    if not exists(os.path.expandvars(ScriptSettings['Python3Path'] + 'scripts\\pip3.exe')):
        raise IOError("Failed to run pip3 -- is your Python3 path correct?")
    
    proc =  subprocess.Popen(cmdline)
    return

def Init():
    global cmd
    global ScriptSettings

    #   Load settings
    SettingsFile = os.path.join(os.path.dirname(__file__), "QueueBotSettings.json")
    
    f = open(SettingsFile)
    data = f.read()
    while data[0] != '{':
        data = data[1:len(data)]
    ScriptSettings = json.loads(data)
    f.close()

    return

def Execute(data):
    global cmd
    global ScriptSettings
    #   Check if the propper command is used, the command is not on cooldown and the user has permission to use the command
    if data.IsChatMessage():
        if data.GetParam(0).lower() ==  ScriptSettings['CommandDraw']  and (data.UserName.lower() == Parent.GetChannelName().lower()):
            if ScriptSettings['UseViewerList'] : update_user_list()
            process_draw()
        elif data.GetParam(0).lower() == ScriptSettings['CommandUser'] and data.GetParamCount() >= 2 and ((not Parent.IsOnCooldown(ScriptName,ScriptSettings['CommandUser']) and not  Parent.IsOnUserCooldown(ScriptName,ScriptSettings['CommandUser'],data.UserName)) or Parent.HasPermission(data.UserName, "Moderator","")) and  Parent.HasPermission(data.UserName, ScriptSettings['PermissionUserOther'], ""):
            process_user_other(data)
            Parent.AddUserCooldown(ScriptName, ScriptSettings['CommandUser'], data.UserName, ScriptSettings['CooldownUserIndividual'])
            Parent.AddCooldown(ScriptName,ScriptSettings['CommandUser'],ScriptSettings['CooldownUser'])
        elif data.GetParam(0).lower() == ScriptSettings['CommandUser'] and not Parent.IsOnCooldown(ScriptName,ScriptSettings['CommandUser']) and not Parent.IsOnUserCooldown(ScriptName,ScriptSettings['CommandUser'],data.UserName) and  Parent.HasPermission(data.UserName, ScriptSettings['PermissionUser'], ""):
            process_user(data)
            Parent.AddUserCooldown(ScriptName, ScriptSettings['CommandUser'], data.UserName, ScriptSettings['CooldownUserIndividual'])
            Parent.AddCooldown(ScriptName,ScriptSettings['CommandUser'],ScriptSettings['CooldownUser'])
        elif data.GetParam(0).lower() == ScriptSettings['CommandQueue'] and not Parent.IsOnCooldown(ScriptName,ScriptSettings['CommandQueue']) and  Parent.HasPermission(data.UserName, ScriptSettings['PermissionQueue'], ""):
            process_queue(data)
            Parent.AddCooldown(ScriptName,ScriptSettings['CommandQueue'],ScriptSettings['CooldownQueue'])
    return
    
def ReloadSettings(jsonData):
    global ScriptSettings
    global cmd
    ScriptSettings = json.loads(jsonData)
    ScriptSettings['Username'] = Parent.GetChannelName();
    
    f = open("QueueBotSettings.json", "w")
    f.write(json.dumps(ScriptSettings, indent = 4))
    f.close()
    
    if cmd != None:
        cmd.stdin.write('loadsettings\r\n')
        cmd.stdin.flush()
        cmd.stdout.readline().strip()
    return
    
def Unload():
    global cmd
    if cmd == None:
        return
    if cmd.returncode == None:
        Parent.Log(ScriptName,'Unload killing child process')
        cmd.stdin.write('quit\r\n')
        cmd.stdin.flush()
        cmd.kill()
    cmd = None
    return
    
def ScriptToggled(state):
    if state:
        stary_py3_subprocess()
        return
    Unload()
    return

    
#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
    return

