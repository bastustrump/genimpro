import sys
import sonicevents as se
import grouping as grouping
import recordings as recordings
import numpy as np
import matplotlib.pyplot as plt
import os

onsets1=[]
onsets2=[]

getVar = lambda searchList, ind: [searchList[i] for i in ind]


def analyseTrack(track):

	audiofile = track[2]
	onsets = se.getOnsetsForTrack(track)
	sonicevents,audio = se.getFeaturesForOnsets(onsets,audiofile)
	#sequences = grouping.getSequencesForSonicevents(sonicevents)
	
	
#	for sequence in sequences:
#		events = getVar(sonicevents,sequence)
#		print events
#		print sequence
#		se.showAndPlay(events,audio,sequence)
#	for event in sonicevents:
#		filename = "methods/recording %i/track %i se %i.png" % (track[4],track[3],sonicevents.index(event))
#		directory= "methods/recording %i" % (track[4])
#		if not os.path.exists(directory):
#			os.makedirs(directory)
#		eventPlot(event,filename)
	
	return sonicevents

def eventPlot(event,filename):
	plt.figure()
	t = np.linspace(0, len(event["audio"])/48000.0, num=len(event["audio"]))
	
	#t2 = np.linspace(0, len(se[0]["audio"])/48000.0, num=len(se[0]["features"]["ZCR"]["raw"]))
	
	plt.plot(t,event["audio"],linewidth=0.5)
	#plt.show()
	plt.savefig(filename,dpi=600)
	
def plot(events):	
	
	fig, ax = plt.subplots()
	
	durations = [(events[i]["end"] - events[i]["start"])/float(samplerate) for i in range(len(events))]
	ax.bar(range(len(events)),durations)

	#[(events[i]["end"] for i in range(len(events))]
	#ax.hist(durations, 20, normed=0, histtype='stepfilled', facecolor='g', alpha=0.75)
	plt.show()



def analyseRecording(recordingID,trackNumber=None):
	
	recordingDetails = recordings.getRecordingDetails(recordingID)
	print "ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])
	
	if 'trackNumber' in locals():
		analyseTrack(recordingDetails[4][trackNumber])
		
	else:
		for track in recordingDetails[4]:
			analyseTrack(track)	
			
if __name__ == '__main__':
	
	if len(sys.argv) < 2:
		print "Usage: recording ID"
		recordings.listRecodings()
		sys.exit(1)
	
	recordingID = int(sys.argv[1])
	
	if len(sys.argv) >= 3:
		trackNumber = int(sys.argv[2])
	
	analyseRecording(recordingID,trackNumber)

	
	
	

