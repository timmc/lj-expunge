#!/usr/bin/python
#
# lj-expunge.py - livejournal destroyer
# Based on https://github.com/ghewgill/ljdump by Greg Hewgill <greg@hewgill.com> http://hewgill.com
#
# LICENSE
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2005-2017 Greg Hewgill and contributors

import codecs, os, pickle, pprint, re, shutil, sys, urllib2, xml.dom.minidom, xmlrpclib
from xml.sax import saxutils

try:
    from hashlib import md5
except ImportError:
    import md5 as _md5
    md5 = _md5.new

def calcchallenge(challenge, password):
    return md5(challenge+md5(password).hexdigest()).hexdigest()

def flatresponse(response):
    r = {}
    while True:
        name = response.readline()
        if len(name) == 0:
            break
        if name[-1] == '\n':
            name = name[:len(name)-1]
        value = response.readline()
        if value[-1] == '\n':
            value = value[:len(value)-1]
        r[name] = value
    return r

def getljsession(server, username, password):
    r = urllib2.urlopen(server+"/interface/flat", "mode=getchallenge")
    response = flatresponse(r)
    r.close()
    r = urllib2.urlopen(server+"/interface/flat", "mode=sessiongenerate&user=%s&auth_method=challenge&auth_challenge=%s&auth_response=%s" % (username, response['challenge'], calcchallenge(response['challenge'], password)))
    response = flatresponse(r)
    r.close()
    return response['ljsession']

def dochallenge(server, params, password):
    challenge = server.LJ.XMLRPC.getchallenge()
    params.update({
        'auth_method': "challenge",
        'auth_challenge': challenge['challenge'],
        'auth_response': calcchallenge(challenge['challenge'], password)
    })
    return params

def writelast(journal, lastsync, lastmaxid):
    f = open("%s/.last" % journal, "w")
    f.write("%s\n" % lastsync)
    f.write("%s\n" % lastmaxid)
    f.close()

def lj_expunge(Server, Username, Password, Journal):
    m = re.search("(.*)/interface/xmlrpc", Server)
    if m:
        Server = m.group(1)
    if Username != Journal:
        authas = "&authas=%s" % Journal
    else:
        authas = ""

    try:
        os.mkdir(Journal)
        print "Created sync subdirectory: %s" % Journal
    except:
        pass

    ljsession = getljsession(Server, Username, Password)

    server = xmlrpclib.ServerProxy(Server+"/interface/xmlrpc")

    print "Wiping contents of journal entries for: %s" % Journal

    errors = 0

    lastsync = ""
    lastmaxid = 0
    try:
        f = open("%s/.last" % Journal, "r")
        lastsync = f.readline()
        if lastsync[-1] == '\n':
            lastsync = lastsync[:len(lastsync)-1]
        lastmaxid = f.readline()
        if len(lastmaxid) > 0 and lastmaxid[-1] == '\n':
            lastmaxid = lastmaxid[:len(lastmaxid)-1]
        if lastmaxid == "":
            lastmaxid = 0
        else:
            lastmaxid = int(lastmaxid)
        f.close()
    except:
        pass
    origlastsync = lastsync

    while True:
        r = server.LJ.XMLRPC.syncitems(dochallenge(server, {
            'username': Username,
            'ver': 1,
            'lastsync': lastsync,
            'usejournal': Journal,
        }, Password))
        #pprint.pprint(r)
        if len(r['syncitems']) == 0:
            break
        for item in r['syncitems']:
            # L seems to be an entry, and maybe C is a comment
            if item['item'][0] == 'L':
                print "Overwriting journal entry %s (%s)" % (item['item'], item['action'])
                try:
                    e = server.LJ.XMLRPC.editevent(dochallenge(server, {
                        'username': Username,
                        'ver': 1,
                        'itemid': item['item'][2:],
                        'usejournal': Journal,
                        'event': 'wiped',
                        'subject': 'wiped',
                        'security': 'private',
                        'props': {
                            'taglist': 'wiped', 'current_coords': '0.00N 0.00E',
                            'current_location': 'wiped', 'current_mood': 'wiped',
                            'current_music': 'wiped', 'picture_keyword': 'wiped',
                            'poster_ip': 'wiped', 'useragent': 'wiped'
                        },
                    }, Password))
                    print "Wiped entry %s" % e['url']
                except xmlrpclib.Fault, x:
                    print "Error wiping item: %s" % item['item']
                    pprint.pprint(x)
                    errors += 1
            lastsync = item['time']
            writelast(Journal, lastsync, lastmaxid)

    writelast(Journal, lastsync, lastmaxid)

    if errors > 0:
        print "%d errors" % errors

if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) == 2 else None
    if config_path and os.access(config_path, os.F_OK):
        config = xml.dom.minidom.parse(config_path)
        server = config.documentElement.getElementsByTagName("server")[0].childNodes[0].data
        username = config.documentElement.getElementsByTagName("username")[0].childNodes[0].data
        password = config.documentElement.getElementsByTagName("password")[0].childNodes[0].data
        journal_maybe = config.documentElement.getElementsByTagName("journal")
        if len(journal_maybe) > 0:
            lj_expunge(server, username, password, journal_maybe[0].childNodes[0].data)
        else:
            lj_expunge(server, username, password, username)
    else:
        from getpass import getpass
        print "lj-expunge - livejournal destroyer"
        print
        print "Enter your Livejournal username and password."
        print
        server = "http://livejournal.com"
        username = raw_input("Username: ")
        password = getpass("Password: ")
        print
        print "You may destroy either your own journal, or a community."
        print
        journal = raw_input("Journal to DELETE ENTRIES IN (or hit return to back up '%s'): " % username)
        print
        if journal:
            lj_expunge(server, username, password, journal)
        else:
            lj_expunge(server, username, password, username)
# vim:ts=4 et:	
