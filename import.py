import sqlite3 as lite
import sys
import os
import aifc
import struct
import uuid

db = lite.connect('genImpro.db')
c = db.cursor() 

def import_audio(audiofile,sessionID):

	print "audiofile %s" % (audiofile)
	
	a=aifc.open(audiofile,"r")
	a.getnchannels()
	data = a.readframes(a.getnframes())
	num_samples = a.getnframes() * a.getnchannels()
	if a.getsampwidth() == 1:
		unpacked_samples = struct.unpack(str(num_samples)+'b', data)
		unpacked_samples = [x * 256 for x in unpacked_samples]
	elif a.getsampwidth() == 2:
		unpacked_samples = struct.unpack(str(num_samples)+'h', data)
	else:
		raise Exception("Sorry, wrong samplewidth")
	filenames= []
	channel=0
	for channel in range(0,a.getnchannels()):
		print "channel " + str(channel)
		unpacked_channel = [unpacked_samples[i] for i in range(channel, num_samples, 2)]
		filenames.append(str(sessionID) +  "/" + str(uuid.uuid4()) + ".aiff")
		b=aifc.open(filenames[channel],"w")
		b.setnchannels(1)
		b.setsampwidth(a.getsampwidth())
		b.setframerate(a.getframerate())
		packed_channel = struct.pack(str(len(unpacked_channel))+'h',*unpacked_channel)
		b.writeframes(packed_channel)
		b.close()
	a.close()
	return filenames



if __name__ == '__main__':
	
	c.execute("select ID,sessionID,audiofile1,audiofile2,playerCh1,playerCh2,key from recordings where audiofile2 IS NULL")
	values = c.fetchall()
	
	for recordingID,sessionID,audiofile1,audiofile2,playerCh1,playerCh2,key in values:
		c.execute("select name,instrument from players where ID="+str(playerCh1))
		player1 = c.fetchone()
		if len(player1)==0:
			raise Exception("No valid player ID")
		c.execute("select name,instrument from players where ID="+str(playerCh2))
		player2 = c.fetchone()		
		if len(player2)==0:
			raise Exception("No valid player ID")		

		c.execute("select date,key from sessions where ID="+str(sessionID))
		session = c.fetchone()	
		if len(session)==0:
			raise Exception("No valid session ID")	
							
		print "Processing Session ID " + str(sessionID) + " on " + str(session[0]) + " " + str(session[1]) 
		#channel_filenames=["",""]
		channel_filenames = import_audio(str(audiofile1),sessionID)
		print "   Channel 0: Player %i (%s) on %s - file %s" % (playerCh1, player1[0],player1[1],channel_filenames[0])
		print "   Channel 1: Player %i (%s) on %s - file %s" % (playerCh2, player2[0],player2[1],channel_filenames[1])
		
		sqlcommand = "INSERT INTO recordings ('sessionID','audiofile1','audiofile2','playerCh1','playerCh2','key') VALUES (%i,'%s','%s',%i,%i,'%s');" % (sessionID,channel_filenames[0],channel_filenames[1],playerCh1,playerCh2,key)
		#print sqlcommand
		c.execute(sqlcommand)
		db.commit()



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
    
    
