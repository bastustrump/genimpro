#!/usr/bin/env python
import web
import xml.etree.ElementTree as ET
import genimpro as genimpro
import json

#tree = ET.parse('test.xml')
#root = tree.getroot()

db = web.database(dbn='sqlite', db='genImpro.db')

# urls = (
#    '/recordings', 'list_recordings',
#    '/recordings/(.*)', 'get_recording',
#     '/users', 'list_users'
# )
urls = ("/recordings", "list_recordings", 
    '/recordings/(.*)', 'get_recording',
    '/sequences/(.*)', 'sequences',
    '/sessions', 'list_sessions',
    '/sessions/(.*)', 'get_session'
    )


def getRecording(row):
    tracks = []
    recording = {}

    recording["ID"] = row["ID"]
    recording["sessionID"] = row["sessionID"]
    recording["key"] = row["key"]

    #select playerID,audiofile,ID from tracks where recordingID=%i
    trackResults = db.select('tracks',what="playerID,audiofile,ID", where="recordingID=%i" % (row["ID"]))

    for trackRow in trackResults:
        #name,instrument
        playerResults = db.select('players',what="name,instrument", where="ID=%i" % (trackRow["playerID"]))
        playerResults = list(playerResults)
        track = {}
        track["ID"] = trackRow["ID"]
        track["audiofile"] = trackRow["audiofile"]

        track["playerName"] = playerResults[0]["name"]
        track["playerInstrument"] = playerResults[0]["instrument"]

        tracks.append(track)

    recording["tracks"] = tracks

    return recording

class list_sessions:
    def GET(self):
        sessions = []
        results = db.select('sessions')

        for row in results:
            sessions.append(dict(row))

        return json.dumps(sessions)

class list_recordings:
    def GET(self):
        recordings = []
        results = db.select('recordings')

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

class get_session:
    def GET(self,ID):
        recordings = []
        results = db.select('recordings',where="sessionID=%i" % (int(ID)))

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

class get_recording:
    def GET(self,ID):
        recordings = []
        results = db.select('recordings',where="id=%i" % (int(ID)))

        for row in results:
            recordings.append(getRecording(dict(row)))

        return json.dumps(recordings)

class sequences:
    def GET(self,ID):
        sequences = []
        results = db.select('sequences',where="trackID=%i" % (int(ID)))

        for row in results:
            sequences.append(dict(row))

        return json.dumps(sequences)


app = web.application(urls, globals())


if __name__ == '__main__':
    
    app.run()



#https://zenodo.org/deposit/29390/file/?file_id=81138b98-51e3-4715-9112-d6dc33b4b477
#https://zenodo.org/deposit/29390/file/?file_id=6c500c49-dd6b-486b-8b30-43fc9f176d7b