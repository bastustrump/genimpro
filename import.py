#! /usr/bin/env python

import sqlite3 as lite
import sys
import os
import aifc
import struct
import uuid
import pprint
import genimpro

db = lite.connect('genImpro.db')
c = db.cursor() 

pp = pprint.PrettyPrinter(indent=4)

def importAudio(audiofile,sessionID):
    
    if not (audiofile.lower().endswith("aiff") | audiofile.lower().endswith("aif")):
        raise Exception("Sorry, wrong fileformat")
    
    print "audiofile %s" % (audiofile)
    
    a=aifc.open(audiofile,"r")
    data = a.readframes(a.getnframes())
    num_samples = a.getnframes() * a.getnchannels()
    
    if a.getsampwidth() == 1:
        unpacked_samples = struct.unpack(str(num_samples)+'b', data)
        unpacked_samples = [x * 256 for x in unpacked_samples]
    elif a.getsampwidth() == 2:
        unpacked_samples = struct.unpack(str(num_samples)+'h', data)
    else:
        raise Exception("Sorry, wrong samplewidth")

    channel=0
    
    sqlcommand = "INSERT INTO recordings ('sessionID','key') VALUES (%i,'%s');" % (sessionID,audiofile)
    #print sqlcommand
    c.execute(sqlcommand)
    db.commit()
    
    recordingID = c.lastrowid 
    
    print "Recording " + str(recordingID) + " in session " + str(sessionID)
    
    for channel in range(0,a.getnchannels()):
        unpacked_channel = [unpacked_samples[i] for i in range(channel, num_samples, 2)]
        filename = str(sessionID) +  "/" + str(uuid.uuid4()) + ".aiff"
        b=aifc.open(filename,"w")
        b.setnchannels(1)
        b.setsampwidth(a.getsampwidth())
        b.setframerate(a.getframerate())
        packed_channel = struct.pack(str(len(unpacked_channel))+'h',*unpacked_channel)
        b.writeframes(packed_channel)
        b.close()
        
        playerID = raw_input("PlayerID for channel " + str(channel) + ":")
        playerID=int(playerID)
        
        if (any(player[0] == playerID for player in players)):
            sqlcommand = "INSERT INTO tracks ('recordingID','playerID','audiofile') VALUES (%i,'%i','%s');" % (recordingID,playerID,filename)
            #print sqlcommand
            c.execute(sqlcommand)
            db.commit()
            player = [player for player in players if player[0] == playerID][0]
            print player
            print "    Channel " + str(channel) + ": " + player[1] + " on " + player[2]
        else:
            raise Exception("Sorry, wrong player ID")
        
    a.close()



if __name__ == '__main__':
	
	c.execute("select id,name,instrument from players")
	players = c.fetchall()

	pp.pprint(players)

	sessionID = int(sys.argv[1])
	files = sys.argv[2:]

	print "Importing Session " + str(sessionID) + "..."

	print files
	for audiofile in files:
		importAudio(audiofile,sessionID)

    genimpro.analyseSession(sessionID)


#with db:
#	cur = db.cursor()
	
	
	

	
#	for audiofile in os.listdir(os.getcwd()+"/1"):
#		if audiofile.endswith(".aif"): 
#			filepath = "1/"+audiofile
#			sqlcommand = "INSERT INTO recordings ('sessionID','audiofile') VALUES (1,'" + filepath + "');"
#			print sqlcommand
#			cur.execute(sqlcommand)
#			
#			continue
#		else:
#			continue   
    
    
