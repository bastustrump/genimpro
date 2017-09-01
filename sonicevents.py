#! /usr/bin/env python
import sys
from aubio import *
from essentia.standard import *
from essentia import Pool, array
import numpy as np
import matplotlib.pyplot as plt
import sqlite3 as lite
import os
import aifc
import uuid, datetime
import recordings as recordings


win_s = 512/2             # fft size
hop_s = win_s/2           # hop size
onset_mode = "hfc" 			#complex

samplerate = 48000.0

def getOnsetsForFile(filename,printDetails=0,t_silence=-95,min_ms=20):

    global samplerate

    s = source(filename)

    o = onset(onset_mode,win_s, hop_s)
    o.set_silence(t_silence)
    o.set_minioi_ms(min_ms)

    multiplier = 512/hop_s
    samplerate=s.samplerate


    onsets = []
    total_frames = 0

    while True:
        samples, read = s()
        #samples = samples * 10.0 #increase loudness for onset detection
        if o(samples):
            onsets.append(o.get_last()*multiplier)
        total_frames += read
        if read < hop_s: break

    if printDetails:
        print "    " + str(len(onsets)) + " onsets found"

    return onsets


def getOnsetsForAudio(audio,printDetails=0):
    from essentia import Pool, array

    od1 = OnsetDetection(method = 'hfc')
    od2 = OnsetDetection(method = 'complex')
    od3 = OnsetDetection(method = 'flux')


    onsetsSamples = []

    w = Windowing(type = 'hann')
    fft = FFT()
    c2p = CartesianToPolar()

    pool = Pool()


    for frame in FrameGenerator(audio, frameSize = 1024, hopSize = 512):
        mag, phase, = c2p(fft(w(frame)))
        pool.add('features.hfc', od1(mag, phase))
        pool.add('features.complex', od2(mag, phase))
        pool.add('features.flux', od3(mag, phase))

    onsets = Onsets()

    onsets_times = onsets(array([ pool['features.hfc'] ,  pool['features.complex'],  pool['features.flux'] ]), [ 5,1,1 ])

    marker = AudioOnsetsMarker(onsets = onsets_times, type = 'beep')
    marked_audio = marker(audio)

    if printDetails:
        print "    " + str(len(onsets_times)) + " onsets found"

    for onset in onsets_times:
        onsetsSamples.append(int(onset * 44100))


    return onsetsSamples


def getOnsetsForTrack(track):

    print "    %s (%s): %s" % (track[0],track[1],track[2])
    audio = recordings.getAudioForTrack(track)
    onsets=[]
    #onsets = getOnsetsForFile(track[2],printDetails=1)
    onsets = getOnsetsForAudio(audio,printDetails=1)

    return (onsets)

def showAndPlay(events,audio,sequence=[]):
	from utility import float2pcm
	import pyaudio

	p = pyaudio.PyAudio()

	stream = p.open(format=2,channels=1,rate=int(samplerate),output=True)

	samples = audio[events[0]["start"]:events[len(events)-1]["end"]]
	startsample = events[0]["start"]
	plt.plot(samples,"b")

	for i in range (0,len(events)):
		print "mark %i from %i to %i" % (sequence[i],events[i]["start"],events[i]["end"])
		plt.text(events[i]["start"], .05, str(sequence[i]))
		plt.axvspan(events[i]["start"]-startsample, events[i]["end"]-startsample, color='red', alpha=(((i+1)%2)*0.5))

	pcmaudio = float2pcm(samples)
	data = struct.pack(str(len(pcmaudio)) + 'h',*pcmaudio)
	stream.write(data)

	plt.show() #block=False

	stream.stop_stream()
	stream.close()

	p.terminate()


def soniceventsForOnsets(onsets,audio,t_loudness=0.5,printDetails=0):
    mono_audio = audio  * 10.0 #normalize
    loudness = essentia.standard.Loudness()

    sonicevents = []
    #onsetStart = onsets[0]

    for i in range(0,len(onsets)):
        if i < len(onsets)-1:
            onsetEnd = onsets[i+1]
        else:
            onsetEnd = len(mono_audio)

        frame = mono_audio[onsets[i]:onsetEnd]

        if (loudness(frame) > t_loudness):
            sonicevents.append({"start":onsets[i],"end":onsetEnd,"loudness":loudness(frame)})
            #onsetStart = onsets[i+1]

    if printDetails:
        print "    " + str(len(sonicevents)) + " sonicevents found"

    for i in range(0,len(sonicevents)-1):
        if sonicevents[i]["end"] is not sonicevents[i+1]["start"]:
            #glue together
            sonicevents[i]["end"]=sonicevents[i+1]["start"]

    return sonicevents


def featuresForSonicevents(sonicevents,audio):

    effectiveDuration = essentia.standard.EffectiveDuration(sampleRate=samplerate,thresholdRatio=0.01)
    loudness = essentia.standard.Loudness()
    zerocrossingrate = essentia.standard.ZeroCrossingRate()
    w = essentia.standard.Windowing()
    spec = essentia.standard.Spectrum()
    centroid = essentia.standard.Centroid()
    SpectralComplexity = essentia.standard.SpectralComplexity(sampleRate=samplerate)
    SpectralRolloff = essentia.standard.RollOff(sampleRate=samplerate)
    SpectralFlux = essentia.standard.Flux()
    Envelope = essentia.standard.Envelope()
    TCToTotal = essentia.standard.TCToTotal()
    LAT = essentia.standard.LogAttackTime()
    Pitch = essentia.standard.PitchYinFFT(sampleRate=samplerate)
    SpectralPeaks = essentia.standard.SpectralPeaks(sampleRate=samplerate)
    Dissonance = essentia.standard.Dissonance()

    for event in sonicevents:
        frame = audio[event["start"]:event["end"]]
        eff_duration = effectiveDuration(frame)

        length_samples = int(eff_duration * samplerate)
        eff_frame = audio[event["start"]:event["start"]+length_samples]
        duration_ratio =  eff_duration / len(frame)

        featurelist = ["Loudness","ZCR","SpectralCentroid","SpectralComplexity","SpectralRolloff","SpectralFlux","Pitch","Roughness"]
        features = {}
        features["effLength"]=length_samples
        features["durationRatio"]=duration_ratio
        features["dynamicBalance"]=TCToTotal(Envelope(frame))
        features["LogAttackTime"]=LAT(Envelope(frame))

        for feature in featurelist:
            features[feature] = {}
            features[feature]["raw"]=[]

        for featureframe in FrameGenerator(eff_frame, frameSize = hop_s, hopSize = hop_s/2):
            features["Loudness"]["raw"].append(loudness(featureframe))
            features["ZCR"]["raw"].append(zerocrossingrate(featureframe))
            spectrum = spec(w(featureframe))
            features["SpectralCentroid"]["raw"].append(centroid(spectrum))
            features["SpectralComplexity"]["raw"].append(SpectralComplexity(spectrum))
            features["SpectralRolloff"]["raw"].append(SpectralRolloff(spectrum))
            features["SpectralFlux"]["raw"].append(SpectralFlux(spectrum))
            peaks = SpectralPeaks(spectrum)
            features["Roughness"]["raw"].append(Dissonance(peaks[0],peaks[1]))

            (pitch,pitchConfidence) = Pitch(spectrum)
            if (pitchConfidence>0.5):
                features["Pitch"]["raw"].append(pitch)
            else:
                features["Pitch"]["raw"].append(0.0)

        #interpolate pitch
        #data = np.asarray(features["Pitch"]["raw"])
        #mask = np.is(data)
        #if len(mask)<len(data):
       	# 	data[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), data[~mask])
       	# 	features["Pitch"]["raw"] = data
       	#	print mask

        for feature in featurelist:
            t = np.linspace(0, len(features[feature]["raw"]), num=len(features[feature]["raw"]))
            if (len(features[feature]["raw"])>0):
	            features[feature]["median"]=np.median(features[feature]["raw"])
	            features[feature]["mean"]=np.mean(features[feature]["raw"])
	            features[feature]["max"]=np.amax(features[feature]["raw"])
	            features[feature]["min"]=np.amin(features[feature]["raw"])
	            features[feature]["variance"]=np.var(features[feature]["raw"])
	            features[feature]["stdev"]=np.std(features[feature]["raw"])
	            features[feature]["corrcoef"]=np.corrcoef(t,features[feature]["raw"])[0][1]

        event["features"]=features

    return sonicevents
