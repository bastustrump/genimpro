from essentia.standard import *
import numpy as np
import simplejson as json

import sqlite3 as lite
#db = lite.connect('genImpro.db')
#c = db.cursor()


import MySQLdb
# db = MySQLdb.connect(host="localhost",
#                      user="genimpro",
#                      passwd="genimpropw#2016",
#                      db="genimpro")
# c = db.cursor()

def getGenepoolForRecording(recordingID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT genepool FROM recordings where ID=%i" % (recordingID)
    c.execute(sqlcommand)
    data = c.fetchone()

    if data[0] is None:
        return None

    #print data[0]

    return json.loads(data[0])

def getGeneticsForRecording(recordingID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT genetics FROM recordings where ID=%i" % (recordingID)
    c.execute(sqlcommand)
    data = c.fetchone()

    if data[0] is None:
        return None

    #print data[0]

    return json.loads(data[0])

def getSoundcell(ID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT start,end,events FROM soundcells where ID=%i" % (ID)
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
        return None

    print data

    return data


def getRecordingDetails(recordingID,printDetails=0):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()

    c.execute("select ID,sessionID,recordingKey,recordingDate from recordings where ID=%i" % (recordingID))
    values = c.fetchone()


    if values==None:
    	raise Exception("No valid ID")

    (recordingID,sessionID,key,date) = values

    if printDetails:
    	print "%i (%s):" % (recordingID,key)

    c.execute("select playerID,audiofile,ID from tracks where recordingID=%i" % (recordingID))
    values = c.fetchall()


    tracks = []

    for track in values:
    	(playerID,audiofile,trackID) = track
    	c.execute("select name,instrument,t_silence,minGapSize from players where ID="+str(playerID))
    	track = c.fetchone()
    	tracks.append([track[0],track[1],audiofile,trackID,recordingID,playerID,track[2],track[3]])

    	if printDetails:
    		print "    %s (%s): %s" % (track[0],track[1],audiofile)

    c.execute("select sessionDate,sessionKey from sessions where ID="+str(sessionID))
    session = c.fetchone()
    values = [recordingID,session[1],session[0],sessionID,tracks,key,date]


    return values

def getAudioForTrack(track,normalize=4):
	#loader = essentia.standard.AudioLoader(filename=track[2])
	#audio,samplerate,x,x,x,x = loader()
	#mono_audio = np.asarray([audio[i][0] for i in range(0,len(audio)-1)])

    monoLoader = essentia.standard.MonoLoader(filename=track[2])

    mono_audio = monoLoader()
    mono_audio = mono_audio  * normalize #normalize

    return mono_audio


def listRecodings(sessionID=None,webservice=0,printDetails=0):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    if sessionID is not None:
        sqlQuery = "select ID from recordings where sessionID=" + str(sessionID)
    else:
        sqlQuery = "select ID from recordings"

    c.execute(sqlQuery)
    values = c.fetchall()

    IDs = []
    recordings = []

    for recordingID in values:
    	recordingDetails = getRecordingDetails(recordingID)

    	if printDetails & (not webservice):
    		print "ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])

    	IDs.append(recordingDetails[0])
    	recordings.append(recordingDetails)

    	if printDetails & (not webservice):
    		for track in recordingDetails[4]:
    			print "    %s (%s): %s" % (track[0],track[1],track[2])

    if (webservice):
    	return json.dumps(recordings)

    return IDs

def createTracks():
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    c.execute("select ID,sessionID,audiofile1,audiofile2,playerCh1,playerCh2,recodingKey from recordings")
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
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    data = json.dumps(sonicevents)

    sqlcommand = "UPDATE tracks SET sonicevents=%s where ID=%i" % (repr(data),track[3])
    c.execute(sqlcommand)
    db.commit()

    print "Updated %i sonicevents for track %i" % (len(sonicevents),track[3])


def updateCellsForTrack(track,cells):
    #clear sequences for track
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "DELETE FROM soundcells where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    db.commit()

    for cell in cells:
        start = cell[0] #sonicevents[sequence[0]]["start"]
        end = cell[1] #sonicevents[sequence[-1]]["end"]
        events = json.dumps(cell)
        sqlcommand = "INSERT INTO soundcells (trackID,start,end,events) values (%i,%i,%i,%s)" % (track[3],start,end,repr(events))
        c.execute(sqlcommand)
        db.commit()

    print "Added %i cells for track %i" % (len(cells),track[3])

# def updateSequencesForTrack(track,sequences,sonicevents):
#     #clear sequences for track
#     sqlcommand = "DELETE FROM sequences where trackID=%i" % (track[3])
#     c.execute(sqlcommand)
#     db.commit()

#     for sequence in sequences:
#         start = sequence[0] #sonicevents[sequence[0]]["start"]
#         end = sequence[1] #sonicevents[sequence[-1]]["end"]
#         events = [] #json.dumps(sequence)
#         sqlcommand = "INSERT INTO sequences (trackID,start,end,events) values (%i,%i,%i,%s)" % (track[3],start,end,repr(events))
#         c.execute(sqlcommand)
#         db.commit()

#     print "Added %i sequences for track %i" % (len(sequences),track[3])


def updatePhenotypesForTrack(track,sequences,phenotypes,dbField='phenotype'):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    for i in range(0,len(sequences)):
        events = json.dumps(sequences[i])
        phenotype = json.dumps(phenotypes[i])
        sqlcommand = "UPDATE soundcells SET %s=%s where trackID=%i AND start=%s" % (dbField,repr(phenotype),track[3],sequences[i][0])
        c.execute(sqlcommand)
        db.commit()

    print "Updated %i phenotypes for track %i" % (len(phenotypes),track[3])


def updateGenotypesForTrack(track,cellBoundaries,genotypes):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    for i in range(0,len(cellBoundaries)):
        events = json.dumps(cellBoundaries[i])
        genotype = json.dumps(genotypes[i].tolist())
        sqlcommand = "UPDATE soundcells SET genotype=%s where trackID=%i AND start=%s" % (repr(genotype),track[3],cellBoundaries[i][0])
        c.execute(sqlcommand)
        db.commit()

    print "Updated %i genotypes for track %i" % (len(genotypes),track[3])




def updateRelationsForTrack(track,sequences,relations):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    for i in range(0,len(relations)):
    	events = json.dumps(sequences[i])
    	relation = json.dumps(relations[i])
        sqlcommand = "UPDATE sequences SET relations=%s where trackID=%i AND events=%s" % (repr(relation),track[3],repr(events))
        c.execute(sqlcommand)
        db.commit()

    print "Updated relations for track %i" % (track[3])

def getLineagesForRecording(recordingID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT ID FROM lineages where recordingID=%i" % (recordingID)
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
        return None

    lineages = []

    for lineage in data:
        lineages.append([lineage[0]])

    return lineages

def getGenotypesForSoundcell(soundcellID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT genotype FROM soundcells where ID=%i" % (int(soundcellID))
    c.execute(sqlcommand)
    data = c.fetchone()

    if data[0] is None:
        return None

    return json.loads(data[0])

def getGenotypesForLineage(lineageID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT genotype FROM soundcells where lineageID=%i" % (int(lineageID))
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

def getGenotypesForTrack(track):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT genotype,ID,start,lineageID,fitness FROM soundcells where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if len(data)==0:
    	return None

    if data[0][0] is None:
    	return None

    genotypes = []
    IDs = []
    start = []
    lineages = []
    fitnessValues = []

    for genotype in data:
        genotypes.append(json.loads(genotype[0]))
        IDs.append(int(genotype[1]))
        start.append(genotype[2])
        lineages.append(genotype[3])
        fitnessValues.append(genotype[4])

    return (IDs,genotypes,start,lineages,fitnessValues)

def getPhenotypesForTrack(track,dbField='phenotypeNormed'):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT %s,ID,start,end FROM soundcells where trackID=%i" % (dbField,track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if len(data)==0:
    	return None

    if data[0][0] is None:
    	return None

    phenotypes = []
    IDs = []
    durations = []


    for phenotype in data:
        phenotypes.append(json.loads(phenotype[0]))
        IDs.append(phenotype[1])
        durations.append(phenotype[3]-phenotype[2])


    return (IDs,phenotypes,durations)


def getSoniceventsForTrack(track):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT sonicevents FROM tracks where ID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchone()

    if data[0] is None:
    	return None

    return json.loads(data[0])

def getSoundcellsForTrack(track):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT start,end,events FROM soundcells where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
        return None

    sequences = []

    for sequence in data:
        sequences.append([sequence[0],sequence[1]])

    return sequences

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True

def getCellsForTrack(track):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT * FROM sequences where trackID=%i" % (track[3])
    c.execute(sqlcommand)
    data = c.fetchall()

    if data is None:
        return None

    cells = []

    for cell in data:
        cellObject = []
        print cell
        for cellElement in list(cell):
            if is_json(cellElement):
                cellObject.append(json.loads(cellElement))
            else:
                cellObject.append(cellElement)
        cells.append(cellObject)

    return cells

def getRecordingIDforTrack(trackID):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    sqlcommand = "SELECT recordingID FROM tracks where ID=%i" % (trackID)
    c.execute(sqlcommand)
    data = c.fetchone()
    return data[0]


def getSequenceIDsForTrack(track):
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
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
    db = MySQLdb.connect(host="localhost",
                     user="genimpro",
                     passwd="genimpropw#2016",
                     db="genimpro")
    c = db.cursor()
    recordingID = getRecordingIDforTrack(trackID)
    recordingDetails = getRecordingDetails(recordingID)
    recordingTracks = recordingDetails[4]

    genotypes = []
    sequenceData = []

    for track in recordingTracks:
        trackGenotypes = getGenotypesForTrack(track)
        if type(trackGenotypes) <> type(None):
            genotypes.extend(trackGenotypes)
            sequenceData.extend(getSequenceIDsForTrack(track))

    return (genotypes,sequenceData)

def getGenome():
    db = MySQLdb.connect(host="localhost",
                 user="genimpro",
                 passwd="genimpropw#2016",
                 db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT variants,clusterGroups FROM genome order by ID desc LIMIT 1 "
    c.execute(sqlcommand)
    data = c.fetchone()

    return json.loads(data[0]), json.loads(data[1])

def getGenepoolNetwork():
    db = MySQLdb.connect(host="localhost",
                 user="genimpro",
                 passwd="genimpropw#2016",
                 db="genimpro")
    c = db.cursor()

    sqlcommand = "SELECT nodes,links FROM genepools order by ID desc LIMIT 1"
    c.execute(sqlcommand)
    data = c.fetchone()

    return json.loads(data[0]), json.loads(data[1])



if __name__ == '__main__':
	listRecodings()
