import sqlite3 as lite
from essentia.standard import *
import numpy as np
import json

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
	
def listRecodings(webservice=0):
	c.execute("select ID from recordings")
	values = c.fetchall()
	
	IDs = []
	recordings = []

	for recordingID in values:
		recordingDetails = getRecordingDetails(recordingID)
		
		if not webservice:
			print "ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])
		
		IDs.append(recordingDetails[0])
		recordings.append(recordingDetails)

		if not webservice:
			for track in recordingDetails[4]:
				print "    %s (%s): %s" % (track[0],track[1],track[2])

	if (webservice):
		return json.dumps(recordings)

	return IDs
		
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


def updateSoniceventsForTrack(track,sonicevents):
    data = json.dumps(sonicevents)
    
    sqlcommand = "UPDATE tracks SET sonicevents=%s where ID=%i" % (repr(data),track[3])
    c.execute(sqlcommand)
    db.commit()
    
    print "Updated %i sonicevents for track %i" % (len(sonicevents),track[3])

def updateSequencesForTrack(track,sequences,sonicevents):
    #clear sequences for track
    sqlcommand = "DELETE FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    db.commit()
    
    for sequence in sequences:
        start = sonicevents[sequence[0]]["start"]
        end = sonicevents[sequence[-1]]["end"]
        events = json.dumps(sequence)
        sqlcommand = "INSERT INTO sequences (trackID,start,end,events) values (%i,%i,%i,%s)" % (track[3],start,end,repr(events))
        c.execute(sqlcommand)
        db.commit()
        
    print "Added %i sequences for track %i" % (len(sequences),track[3])


def updatePhenotypesForTrack(track,sequences,phenotypes):
    
    for i in range(0,len(sequences)):
        events = json.dumps(sequences[i])
        phenotype = json.dumps(phenotypes[i])
        sqlcommand = "UPDATE sequences SET phenotype=%s where trackID=%i AND events=%s" % (repr(phenotype),track[3],repr(events))
        c.execute(sqlcommand)
        db.commit()
        
    print "Updated %i phenotypes for track %i" % (len(phenotypes),track[3])


def updateGenotypesForTrack(track,sequences,genotypes):
    
    for i in range(0,len(sequences)):
        events = json.dumps(sequences[i])
        genotype = json.dumps(genotypes[i].tolist())
        sqlcommand = "UPDATE sequences SET genotype=%s where trackID=%i AND events=%s" % (repr(genotype),track[3],repr(events))
        c.execute(sqlcommand)
        db.commit()
        
    print "Updated %i genotypes for track %i" % (len(genotypes),track[3])


def updateRelationsForTrack(track,sequences,relations):
    
    for i in range(0,len(relations)):
    	events = json.dumps(sequences[i])
    	relation = json.dumps(relations[i])
        sqlcommand = "UPDATE sequences SET relations=%s where trackID=%i AND events=%s" % (repr(relation),track[3],repr(events))
        c.execute(sqlcommand)
        db.commit()
        
    print "Updated relations for track %i" % (track[3])


def getGenotypesForTrack(track):
    sqlcommand = "SELECT genotype FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if len(data)==0:
    	return None

    if data[0][0] is None:
    	return None

    genotypes = []
    
    for genotype in data:
        genotypes.append(json.loads(genotype[0]))
        
    return genotypes

def getPhenotypesForTrack(track):
    sqlcommand = "SELECT phenotype FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if len(data)==0:
    	return None

    if data[0][0] is None:
    	return None

    phenotypes = []
    
    for phenotype in data:
        phenotypes.append(json.loads(phenotype[0]))
        
    return phenotypes

		
def getSoniceventsForTrack(track):
    sqlcommand = "SELECT sonicevents FROM tracks where ID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchone()

    if data[0] is None:
    	return None

    return json.loads(data[0])

def getSequencesForTrack(track):
    sqlcommand = "SELECT events FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
    	return None

    sequences = []
    
    for sequence in data:
        sequences.append(json.loads(sequence[0]))
        
    return sequences

def getRecordingIDforTrack(trackID):
    sqlcommand = "SELECT recordingID FROM tracks where ID=%i" % (trackID)
    c.execute(sqlcommand)
    data = c.fetchone()
    return data[0]



def getSequenceIDsForTrack(track):
    sqlcommand = "SELECT ID,start,end FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
        return None

    sequences = []
    
    for sequence in data:
        sequence = list(sequence)
        sequence.append(track[3])
        sequences.append(sequence)
        
    return sequences

def prepareDataForRelations(trackID):
    recordingID = getRecordingIDforTrack(trackID)
    recordingDetails = getRecordingDetails(recordingID)
    recordingTracks = recordingDetails[4]
    
    genotypes = []
    sequenceData = []
    
    for track in recordingTracks:
        genotypes.extend(getGenotypesForTrack(track))
        sequenceData.extend(getSequenceIDsForTrack(track))
    
    return (genotypes,sequenceData)

def getGenome():
    sqlcommand = "SELECT CNTR FROM genome order by ID desc LIMIT 1"
    c.execute(sqlcommand)
    data = c.fetchone()

    return np.asarray(json.loads(data[0]))
    		
if __name__ == '__main__':
	listRecodings()
	
	