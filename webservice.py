#!/usr/bin/env python
import web
import xml.etree.ElementTree as ET
import genimpro as genimpro
import json

import numpy as np
import pydub
import cStringIO
import StringIO
import base64
import os

samplerate=44100.0

peakShift = 1325
#tree = ET.parse('test.xml')
#root = tree.getroot()

#db = web.database(dbn='sqlite', db='genImpro.db')


# import MySQLdb
# db = MySQLdb.connect(host="localhost",
#                      user="genimpro",
#                      passwd="genimpropw#2016",
#                      db="genimpro")
# c = db.cursor()

urls = ("/recordings", "list_recordings",
    "/tracks", "list_tracks",
    '/recordings/(.*)', 'get_recording',
    '/segments/(.*)', 'segments',
    '/editedSegments/(.*)', 'editedSegments',
    '/soundcells/(.*)', 'soundcells',
    '/soundcellAudio/(.*)', 'soundcellAudio',
    '/testAudio/(.*)', 'testAudio',
    '/testAudioForRecording/(.*)', 'testAudioForRecording',
    '/audioForRecording/(.*)', 'audioForRecording',
    '/sessions', 'list_sessions',
    '/sessions/(.*)', 'get_session',
    '/genetics/(.*)', 'get_genetics',
    '/genepoolNetworks', 'get_genepoolNetworks',
    '/genome', 'get_genome'
    )


def getRecording(row):

    db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
    tracks = []
    recording = {}

    recording["ID"] = row["ID"]
    recording["sessionID"] = row["sessionID"]
    recording["key"] = row["recordingKey"]

    #select playerID,audiofile,ID from tracks where recordingID=%i
    trackResults = db.select('tracks',what="playerID,audiofile,ID", where="recordingID=%i" % (row["ID"]))

    for trackRow in trackResults:
        #name,instrument
        playerResults = db.select('players',what="name,instrument,playerKey", where="ID=%i" % (trackRow["playerID"]))
        playerResults = list(playerResults)
        track = {}
        track["ID"] = trackRow["ID"]
        track["audiofile"] = trackRow["audiofile"]
        track["playerName"] = playerResults[0]["name"]
        track["playerInstrument"] = playerResults[0]["instrument"]
        track["playerKey"] = playerResults[0]["playerKey"]
        tracks.append(track)

    recording["tracks"] = tracks

    return recording


def mp3forRecoding(recordingID,samplerate=44100.0):

    recording = genimpro.recordings.getRecordingDetails(recordingID)

    tracksAudio=[]
    for i,track in enumerate(recording[4]):
        filename = track[2]

        if os.path.isfile(filename):
            aiffAudio = pydub.AudioSegment.from_file(filename,"aiff")
        else:
            mp3filename = os.path.splitext(filename)[0] + ".mp3"
            aiffAudio = pydub.AudioSegment.from_file(mp3filename,"mp3")
        
        aiffAudio = aiffAudio + 10
        tracksAudio.append(aiffAudio)
        #aiffAudio.export(mp3filename, format="mp3")

    left = tracksAudio[0].pan(-1.0)
    right = tracksAudio[1].pan(1.0)

    left = left
    right = right

    combined = left.overlay(right)

    mp3audio = combined.export(cStringIO.StringIO(), format='mp3')
    mp3audio.reset()
    mp3audio = mp3audio.read()

    src = '<source controls src="data:audio/mpeg;base64,{base64}" type="audio/mpeg" />'.format(base64=base64.encodestring(mp3audio))

    return src

class testAudioForRecording:
    def GET(self,ID):

        return """
        <body>
        <audio controls="controls" style="width:600px" >
          {audio}
        </audio>
        </body>
        """.format(audio=mp3forRecoding(int(ID)))

class audioForRecording:
    def GET(self,ID):

        return mp3forRecoding(int(ID))


def mp3slice(filename,start,end,samplerate=44100.0):
    if os.path.splitext(filename)[1]==".mp3":
        audio = pydub.AudioSegment.from_mp3(filename)
    elif os.path.splitext(filename)[1]==".aiff":
        if os.path.exists(filename):
            audio = pydub.AudioSegment.from_file(filename,"aiff")
        else:
            mp3filename = os.path.splitext(filename)[0] + ".mp3"
            audio = pydub.AudioSegment.from_mp3(mp3filename)
    else:
        print "no valid filetype"
        return

    one_second_silence = pydub.AudioSegment.silent(duration=500)

    audioslice=one_second_silence + audio[(start/samplerate)*1000:(end/samplerate)*1000]

    mp3audio = audioslice.export(cStringIO.StringIO(), format='mp3')
    mp3audio.reset()
    mp3audio = mp3audio.read()

    src = '<source controls src="data:audio/mpeg;base64,{base64}" type="audio/mpeg" />'.format(base64=base64.encodestring(mp3audio))

    return src

class list_sessions:
    def GET(self):
        sessions = []
        results = db.select('sessions')

        for row in results:
            sessions.append(dict(row))

        return json.dumps(sessions)

class get_genome:
    def GET(self):
        return json.dumps(genimpro.recordings.getGenome())

class get_genepoolNetworks:
    def GET(self):
        return json.dumps(genimpro.recordings.getGenepoolNetwork())

class list_recordings:
    def GET(self):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        recordings = []
        results = db.select('recordings',what="ID,recordingKey,recordingDate,sessionID")

        for row in results:
            recordings.append(row)

        return json.dumps(recordings)

class list_tracks:
    def GET(self):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        recordings = []
        results = db.select('recordings')

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

class get_genetics:
    def GET(self,ID):
        return json.dumps(genimpro.geneticsForVisualisation(int(ID)))

class get_session:
    def GET(self,ID):
        recordings = []
        results = db.select('recordings',where="sessionID=%i" % (int(ID)))

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

class get_recording:
    def GET(self,ID):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        recordings = []
        results = db.select('recordings',where="id=%i" % (int(ID)))

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

def tracksIDsForRecording(recordingID):
    db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
    results = db.select('tracks',where="recordingID=%i" % (int(recordingID)))
    tracks = []
    for row in results:
        tracks.append(row["ID"])

    return tracks

class soundcells:
    def GET(self,ID):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        soundcells = []
        print tracksIDsForRecording(ID)
        for trackID in tracksIDsForRecording(ID):
            results = db.select('soundcells',where="trackID=%i" % (int(trackID)))

            for row in results:
                phenotype = json.loads(row["phenotypeNormed"])
                genotype = json.loads(row["genotype"])
                soundcells.append({"genotype":genotype,"phenotype":phenotype,"ID":row["ID"],"trackID":row["trackID"]})

        return json.dumps(soundcells)

class editedSegments:
    def POST(self,ID):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        data = json.loads(web.data())

        segments1 = np.asarray(data[0]) * samplerate - peakShift
        segments2 = np.asarray(data[1]) * samplerate - peakShift
        segments1 = segments1.tolist()
        segments2 = segments2.tolist()

        db.update('recordings', where="id=%i" % (int(ID)), soundcells_edited=json.dumps([segments1,segments2]))

class segments:
    def GET(self,ID):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        segments1 = []
        segments2 = []

        results = db.select('recordings',where="id=%i" % (int(ID)))

        for row in results:
            recording = getRecording(dict(row))
            tracksIDs=[recording["tracks"][0]["ID"],recording["tracks"][1]["ID"]]

        results = db.select('soundcells',where="trackID=%i" % (int(tracksIDs[0])))

        for row in results:
            segments1.append({'startTime':(row["start"]+peakShift)/samplerate,'endTime':(row["end"]+peakShift)/samplerate,'editable':True})

        results = db.select('soundcells',where="trackID=%i" % (int(tracksIDs[1])))
        for row in results:
            segments2.append({'startTime':(row["start"]+peakShift)/samplerate,'endTime':(row["end"]+peakShift)/samplerate,'editable':True})


        return json.dumps([segments1,segments2])

class soundcellAudio:
    def GET(self,ID):
        db = web.database(dbn='mysql', user='genimpro', pw='genimpropw#2016', db='genimpro')
        sequenceQuery = db.select('soundcells',where="ID=%i" % (int(ID)))
        row = sequenceQuery[0]
        trackID = row["trackID"]
        start =row["start"]
        end =row["end"]
        filenameQuery = db.select('tracks',where="ID=%i" % (trackID))

        filename = filenameQuery[0]["audiofile"]

        return mp3slice(filename,start,end)


app = web.application(urls, globals())


if __name__ == '__main__':

    app.run()



#https://zenodo.org/deposit/29390/file/?file_id=81138b98-51e3-4715-9112-d6dc33b4b477
#https://zenodo.org/deposit/29390/file/?file_id=6c500c49-dd6b-486b-8b30-43fc9f176d7b
