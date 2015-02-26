import sqlite3 as lite
from essentia.standard import *
import numpy as np
db = lite.connect('genImpro.db')
c = db.cursor() 

def getRecordingDetails(recordingID,printDetails=0):
	c.execute("select ID,sessionID,key from recordings where ID=%i" % (recordingID))
	values = c.fetchone()
	if values==None:
		raise Exception("No valid ID")
		
	(recordingID,sessionID,key) = values

	if printDetails:
		print "%i (%s):" % (recordingID,key)	

	c.execute("select playerID,audiofile,ID from tracks where recordingID=%i" % (recordingID))
	values = c.fetchall()

	tracks = []

	for track in values:
		(playerID,audiofile,trackID) = track
		c.execute("select name,instrument from players where ID="+str(playerID))
		track = c.fetchone()
		tracks.append([track[0],track[1],audiofile,trackID,recordingID])

		if printDetails:
			print "    %s (%s): %s" % (track[0],track[1],audiofile)

	c.execute("select date,key from sessions where ID="+str(sessionID))
	session = c.fetchone()
	values = [recordingID,session[1],session[0],sessionID,tracks]



	return values

def getAudioForTrack(track):
	loader = essentia.standard.AudioLoader(filename=track[2])
	audio,samplerate,x,x,x,x = loader()
	mono_audio = np.asarray([audio[i][0] for i in range(0,len(audio)-1)])
	mono_audio = mono_audio  * 4.0 #normalize
	return mono_audio
	
def listRecodings():
	c.execute("select ID from recordings")
	values = c.fetchall()
	
	for recordingID in values:
		recordingDetails = getRecordingDetails(recordingID)
		print "ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])
		
		for track in recordingDetails[4]:
			print "    %s (%s): %s" % (track[0],track[1],track[2])
		
		
def createTracks():
	c.execute("select ID,sessionID,audiofile1,audiofile2,playerCh1,playerCh2,key from recordings")
	values = c.fetchall()
	
	for recording in values:
		(recordingID,sessionID,audiofile1,audiofile2,playerCh1,playerCh2,key) = recording
		sqlcommand = "INSERT INTO tracks ('recordingID','playerID','audiofile') VALUES (%i,%i,'%s');" % (recordingID,playerCh1,audiofile1)
		print sqlcommand
		c.execute(sqlcommand)
		db.commit()

		sqlcommand = "INSERT INTO tracks ('recordingID','playerID','audiofile') VALUES (%i,%i,'%s');" % (recordingID,playerCh2,audiofile2)
		print sqlcommand
		c.execute(sqlcommand)
		db.commit()
		
		
if __name__ == '__main__':
	listRecodings()
	
	