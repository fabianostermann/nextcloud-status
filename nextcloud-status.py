#!/usr/bin/python3
#
# This program aims to implement a nextcloud status request command-line tool that
# works as similar as possible to 'dropbox status'.
# Most of the time, it just prints 'Up to date' or 'Syncing..' to stdout.
#
# The parts for connecting and querying the nextcloud client socket are borrowed from
# the OwnCloud integration to Nautilus by Klaas Freitag, see:
# https://github.com/nextcloud/desktop/blob/master/shell_integration/nautilus/syncstate.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# If you want to implement other socket info/action requests, you can find a list at:
# https://github.com/nextcloud/desktop/blob/master/src/gui/socketapi/socketapi.h

def DEBUG(msg):
    #print("DEBUG:", msg)
    pass

import sys
python3 = sys.version_info[0] >= 3

import os
import urllib
if python3:
    import urllib.parse
import socket
import tempfile
import time

import configparser

#from gi.repository import GObject, Nautilus

# Note: setappname.sh will search and replace 'ownCloud' on this file to update this line and other
# occurrences of the name
appname = 'Nextcloud'

### startup info silenced
#print("Initializing "+appname+"-client-nautilus extension")
#print("--> This version of "+appname+"-client-nautilus was changed by @fabianostermann")
#print("Using python version {}".format(sys.version_info))

# determine nextcloud path, default is "~/Nextcloud"
nextcloud_pathes = []
try:
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.config/Nextcloud/nextcloud.cfg"))
    for key, value in config["Accounts"].items():
        if "localpath" in key:
            path = os.path.expanduser(value)
            path = os.path.realpath(path)
            nextcloud_pathes.append(path)
except:
    nextcloud_pathes = ["~/Nextcloud"]
    print("Could not read config, falling back to default path",nextcloud_pathes,"..")

DEBUG("Found nextcloud folders:")
DEBUG(nextcloud_pathes)

def get_local_path(url):
    if url[0:7] == 'file://':
        url = url[7:]
    unquote = urllib.parse.unquote if python3 else urllib.unquote
    return unquote(url)

def get_runtime_dir():
    """Returns the value of $XDG_RUNTIME_DIR, a directory path.

    If the value is not set, returns the same default as in Qt5
    """
    try:
        return os.environ['XDG_RUNTIME_DIR']
    except KeyError:
        fallback = os.path.join(tempfile.gettempdir(), 'runtime-' + os.environ['USER'])
        return fallback


class SocketConnect:#(GObject.GObject):
    def __init__(self):
        #GObject.GObject.__init__(self)
        self.connected = False
        self.registered_paths = {}
        self._watch_id = 0
        self._sock = None
        self._listeners = [self._update_registered_paths, self._get_version]
        self._remainder = ''.encode() if python3 else ''
        self.protocolVersion = '1.0'
        self.nautilusVFSFile_table = {}  # not needed in this object actually but shared
                                         # all over the other objects.

        # returns true when one should try again!
        if self._connectToSocketServer():
            self.timeout_add(5, self._connectToSocketServer)
            
        #print("Connected!" if self.connected else "Did not connect.")

    def reconnect(self):
        self._sock.close()
        self.connected = False
        #GObject.source_remove(self._watch_id)
        self.timeout_add(5, self._connectToSocketServer)

    def timeout_add(time_secs, func):
        time.sleep(time_secs)
        func()

    def sendCommand(self, cmd):
        # print("Server command: " + cmd)
        if self.connected:
            try:
                self._sock.send(cmd.encode() if python3 else cmd)
                #print("Sended:", cmd)
            except:
                print("Sending failed.")
                self.reconnect()
        else:
            print("Cannot send, not connected!")

    def addListener(self, listener):
        self._listeners.append(listener)

    def _connectToSocketServer(self):
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock_file = os.path.join(get_runtime_dir(), appname, "socket")
            try:
                self._sock.connect(sock_file) # fails if sock_file doesn't exist
                self.connected = True
                #self._watch_id = GObject.io_add_watch(self._sock, GObject.IO_IN, self._handle_notify)

                self.sendCommand('VERSION:\n')
                self.sendCommand('GET_STRINGS:\n')
                
                #print("Found socket at:", sock_file)
                return False  # Don't run again
            except Exception as e:
                #print("Could not connect to unix socket " + sock_file + ". " + str(e))
                print("Nextcloud isn't running!")
                exit()
        except Exception as e:  # Bad habbit
            print("Connect could not be established, try again later.")
            self._sock.close()

        return True  # Run again, if enabled via timeout_add()

    # Reads data that becomes available.
    # New responses can be accessed with get_available_responses().
    # Returns false if no data was received within timeout
    def read_socket_data_with_timeout(self, timeout):
        self._sock.settimeout(timeout)
        try:
            self._remainder += self._sock.recv(1024)
        except socket.timeout:
            return False
        else:
            return True
        finally:
            self._sock.settimeout(None)

    # Parses response lines out of collected data, returns list of strings
    def get_available_responses(self):
        end = self._remainder.rfind(b'\n')
        if end == -1:
            return []
        data = self._remainder[:end]
        self._remainder = self._remainder[end+1:]
        data = data.decode() if python3 else data
        return data.split('\n')

    # Notify is the raw answer from the socket
    def _handle_notify(self, source, condition):
        # Blocking is ok since we're notified of available data
        self._remainder += self._sock.recv(1024)

        if len(self._remainder) == 0:
            return False

        for line in self.get_available_responses():
            self.handle_server_response(line)

        return True  # Run again

    def handle_server_response(self, line):
        # print("Server response: " + line)
        parts = line.split(':')
        action = parts[0]
        args = parts[1:]

        for listener in self._listeners:
            listener(action, args)

    def _update_registered_paths(self, action, args):
        if action == 'REGISTER_PATH':
            self.registered_paths[args[0]] = 1
        elif action == 'UNREGISTER_PATH':
            del self.registered_paths[args[0]]

            # Check if there are no paths left. If so, its usual
            # that mirall went away. Try reconnecting.
            if not self.registered_paths:
                self.reconnect()

    def _get_version(self, action, args):
        if action == 'VERSION':
            self.protocolVersion = args[1]


def translate_command(cmd):
    """ 
    Translate command to human readable format.
    Aim is to be as identical as possible to the outputs from 'dropbox status'.
    """
    answers = { 'OK'        : 'Up to date',
               'SYNC'      : 'Syncing..',
               'NEW'       : 'Syncing..',
               'IGNORE'    : 'WARNING..',
               'ERROR'     : 'ERROR..',
               'OK+SWM'    : 'Up to date',
               'SYNC+SWM'  : 'Syncing..',
               'NEW+SWM'   : 'Syncing..',
               'IGNORE+SWM': 'WARNING..',
               'ERROR+SWM' : 'ERROR..',
               'NOP'       : 'No operation (the nextcloud path could be wrong. Is '+";".join(nextcloud_pathes)+' correct?)'
               }
    return answers[cmd]

def handle_commands(action, args):
    #answer = args[0]  # For debug only
    #print("Action " + action + " -> got " + answer)  # For debug only
    global RECV_ANSWER
    if action == 'STATUS':
        state = args[0]
        
        print(translate_command(state))
        RECV_ANSWER = True
        
        if len(nextcloud_pathes) == 1:      
            DEBUG("Exiting on purpose.")
            exit()

socketConnect = SocketConnect()
socketConnect.addListener(handle_commands)   

RECV_ANSWER = False
for nextcloud_path in nextcloud_pathes:
    if len(nextcloud_pathes) > 1:
        print(nextcloud_path, end=": ")

    RECV_ANSWER = False

    DEBUG("handle notify..")
    socketConnect.sendCommand("RETRIEVE_FOLDER_STATUS:"+nextcloud_path+"\n")
    time.sleep(0.1)
    socketConnect._handle_notify(None, None)

    # wait 3 seconds for an answer
    wait_count = 3
    while wait_count>0 and not RECV_ANSWER:
        DEBUG(".")
        time.sleep(0.2)
        wait_count -= 0.2
        
    if not RECV_ANSWER:  
        print("No answer from socket.")

