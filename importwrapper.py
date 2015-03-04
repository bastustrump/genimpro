from __future__ import division, print_function, absolute_import

import struct
import warnings    
import sys
import numpy as np
import matplotlib.pyplot as plt
import os
import genimpro as genimpro
from pprint import pprint
import struct
from IPython.core.display import HTML
import scipy.constants as const
import scipy
from scipy.io import wavfile
import matplotlib.transforms as transforms
import matplotlib.cm as cm
from IPython.display import Audio
from IPython.display import Math
import IPython.core.display
import pydub
import cStringIO
import StringIO
import base64

samplerate=48000.0

np.seterr(all='ignore')

global audio

def float2pcm(sig, dtype='int16'):
    """Convert floating point signal with a range from -1 to 1 to PCM.

    Parameters
    ----------
    sig : array_like
        Input array, must have floating point type.
    dtype : data type, optional
        Desired (integer) data type.

    Returns
    -------
    ndarray
        integer data.

    See Also
    --------
    pcm2float, dtype

    """
    # TODO: allow unsigned (e.g. 8-bit) data

    sig = np.asarray(sig)
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind != 'i':
        raise TypeError("'dtype' must be signed integer type")

    return (sig * np.iinfo(dtype).max).astype(dtype)

def wavPlayer(data, rate):
    
    silence = np.zeros(10000)
    audio = []
    audio.extend(silence)
    audio.extend(data)

    data = float2pcm(audio)

    buffer = StringIO.StringIO()
    buffer.write(b'RIFF')
    buffer.write(b'\x00\x00\x00\x00')
    buffer.write(b'WAVE')
    buffer.write(b'fmt ')
    if data.ndim == 1:
        noc = 1
    else:
        noc = data.shape[1]
    bits = data.dtype.itemsize * 8
    sbytes = rate*(bits // 8)*noc
    ba = noc * (bits // 8)
    buffer.write(struct.pack('<ihHIIHH', 16, 1, noc, rate, sbytes, ba, bits))

    # data chunk
    buffer.write(b'data')
    buffer.write(struct.pack('<i', data.nbytes))

    if data.dtype.byteorder == '>' or (data.dtype.byteorder == '=' and sys.byteorder == 'big'):
        data = data.byteswap()

    buffer.write(data.tostring())
    size = buffer.tell()
    buffer.seek(4)
    buffer.write(struct.pack('<i', size-8))
    
    val = buffer.getvalue()
    
    wave = pydub.AudioSegment.from_wav(cStringIO.StringIO(val))    
    mp3audio = wave.export(cStringIO.StringIO(), format='mp3')
    mp3audio.reset()
    mp3audio = mp3audio.read()

    # src = """
    # <body>
    # <audio controls="controls" style="width:600px" >
    #   <source controls src="data:audio/wav;base64,{base64}" type="audio/wav" />
    #   Your browser does not support the audio element.
    # </audio>
    # </body>
    # """.format(base64=base64.encodestring(val))


    src = """
    <body>
    <audio controls="controls" style="width:600px" >
      <source controls src="data:audio/mpeg;base64,{base64}" type="audio/mpeg" />
      Your browser does not support the audio element.
    </audio>
    </body>
    """.format(base64=base64.encodestring(mp3audio))
    
    IPython.core.display.display(HTML(src))


# def plotFeature(feature,event,t_features,color,context,x,y,h_columns):
#     context.plot(t_features,event["features"][feature]["raw"],label=feature,linewidth=2,color=color)
#     context.axhline(y=event["features"][feature]["mean"],linewidth=1,color=color)
#     context.errorbar(x, y, yerr=event["features"][feature]["stdev"], fmt='-o',color=color,linewidth=5)
#     context.plot(t_features,event["features"][feature]["mean"]+(t_features*event["features"][feature]["corrcoef"]),linewidth=1,color=color,ls='dashed')
#     context.text(x + h_columns/10, y*1.1, 'mean = %f\nstdev = %f\ncorrcoeff = %f' % (event["features"][feature]["mean"],event["features"][feature]["stdev"],event["features"][feature]["corrcoef"]), style='italic', bbox={'facecolor':color, 'alpha':0.7, 'pad':10})

# def plotWithPlayer(event):
#     t_audio = np.linspace(0, len(event["audio"])/samplerate, num=len(event["audio"]))
#     t_features = np.linspace(0, len(event["audio"])/samplerate, num=len(event["features"]["Loudness"]["raw"]))

#     colors = cm.rainbow(np.linspace(0, 1, len(event["features"])-1))
#     colorindex = 0
    
#     fig = plt.figure(figsize=(18, 12), dpi=400)
#     ax = fig.add_subplot(111)
#     plt.xlabel('Zeit (Sekunden)')

#     ax.plot(t_audio,event["audio"],'0.5',label="Audio Waveform",linewidth=0.7)
#     h_columns=t_features[-1]/6
    
#     for feature in event["features"]:
#         if type(event["features"][feature])==type(dict()):
#             x = h_columns*(colorindex+1)
#             y = event["features"][feature]["mean"]
#             color = colors[colorindex]
            
#             if event["features"][feature]["max"] > 1.0:
#                 ax2 = ax.twinx()
#                 ax2.set_ylabel(feature,color=color)
#                 plotFeature(feature,event,t_features,color,ax2,x,y,h_columns)
#             else:
#                 plotFeature(feature,event,t_features,color,ax,x,y,h_columns)
#             colorindex+=1
               
#             #ax.legend(loc=4)
            
#     lines, labels = ax.get_legend_handles_labels()
#     lines2, labels2 = ax2.get_legend_handles_labels()
#     ax.legend(lines+lines2, labels+labels2, loc=0)
#     plt.tight_layout()
    
#     wavPlayer(event["audio"],samplerate)

def plotOnsets(onsetRange,audio):
    plt.figure(figsize=(20, 8), dpi=400)
    plt.plot(audio[onsetRange[0]:onsetRange[-1]],'0.5',label="Audio Waveform",linewidth=0.7)
    for onset in onsetRange:
        plt.axvline(x=onset-onsetRange[0],linewidth=0.5,color='g')
    wavPlayer(audio[onsetRange[0]:onsetRange[-1]],samplerate)

def plotOnsetsAndSonicevents(onsetRange,sonicevents,audio):
    plt.figure(figsize=(20, 8), dpi=400)
    plt.plot(audio[onsetRange[0]:onsetRange[-1]],'0.5',label="Audio Waveform",linewidth=0.7)
    SELoudness=[]
    SELoudnessTimestamp=[]

    for onset in onsetRange:
        plt.axvline(x=onset-onsetRange[0],linewidth=0.5,color='g')
    ax2 = plt.twinx()
    for i in range(0,len(sonicevents)):
        if onsetRange[0]<=sonicevents[i]["start"]<onsetRange[-1]:
            plt.axvline(x=sonicevents[i]["start"]-onsetRange[0],linewidth=2,color='r',alpha=0.5)
            SELoudness.append(sonicevents[i]["loudness"])
            SELoudnessTimestamp.append(sonicevents[i]["start"]-onsetRange[0])
            
    ax2.plot(SELoudnessTimestamp,SELoudness,color='b',marker='o',lw=0,ms=10)
    ax2.set_ylabel("loudness",color='b')
    wavPlayer(audio[onsetRange[0]:onsetRange[-1]],samplerate)

def plotStatistics(feature,event,t_features,color,context,x,y,h_columns):
    #context.plot(t_features,event["features"][feature]["raw"],label=feature,linewidth=2,color=color)
    context.axhline(y=event["features"][feature]["mean"],linewidth=1,color=color)
    context.errorbar(x, y, yerr=event["features"][feature]["stdev"], fmt='-o',color=color,linewidth=5)
    context.plot(t_features,event["features"][feature]["mean"]+(t_features*event["features"][feature]["corrcoef"]),linewidth=1,color=color,ls='dashed')
    context.text(x + h_columns/10, y*1.1, 'mean = %f\nstdev = %f\ncorrcoeff = %f' % (event["features"][feature]["mean"],event["features"][feature]["stdev"],event["features"][feature]["corrcoef"]), style='italic', bbox={'facecolor':color, 'alpha':0.7, 'pad':10})


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.itervalues():
        sp.set_visible(False)

def plotFeaturesWithPlayer(events,audio,showFeatures=[],showNumbers=0,showStatistics=0):

    samples = audio[events[0]["start"]:events[len(events)-1]["end"]]
    startsample = events[0]["start"]
    t_audio = np.linspace(0, len(samples)/samplerate, num=len(samples))

    if (showFeatures==[]) & showStatistics:
        for feature in events[0]["features"]:
            showFeatures.append(feature)

    #create different colors for feature distinction
    colors = cm.rainbow(np.linspace(0, 1, len(events[0]["features"])))
    colorindex = 0
    featureindex = 0
    
    fig = plt.figure(figsize=(35, 20), dpi=400)
    ax1 = fig.add_subplot(221)
    plt.xlabel('time (seconds)')
    plt.plot(t_audio,samples,'0.7',label="Audio Waveform",linewidth=2,clip_on=False)
    trans = transforms.blended_transform_factory(ax1.transData, ax1.transAxes)
    
    ax = {}
    featurecolor={}
    for feature in events[0]["features"]:
        featurecolor[feature] = colors[colorindex]
        colorindex+=1
        if (feature in showFeatures) & (type(events[0]["features"][feature])==type(dict())):
            ax[feature]=plt.twinx()
            ax[feature].plot(0,0,label=feature,linewidth=2,color=featurecolor[feature])
            
    for i in range (0,len(events)):

        markBegin = (events[i]["start"]-startsample)/samplerate
        markEnd = (events[i]["start"]-startsample+events[i]["features"]["effLength"])/samplerate
        eventEnd = (events[i]["start"]-startsample + (events[i]["end"]-events[i]["start"]))/samplerate
        
        featureindex = 0
        spineindex = 0
        for feature in events[i]["features"]:
            if (type(events[i]["features"][feature])==type(dict())) & (feature in showFeatures):
                t_feature = np.linspace(markBegin, markEnd, num=len(events[i]["features"][feature]["raw"]))
                
                tkw = dict(size=1, width=1)
                if events[i]["features"][feature]["max"] > 1.0:
                    feature_ax=ax[feature]
                    feature_ax.plot(t_feature,events[i]["features"][feature]["raw"],linewidth=1.6,color=featurecolor[feature])
                    make_patch_spines_invisible(feature_ax)
                    feature_ax.tick_params(axis='y', colors=featurecolor[feature], **tkw)
                    feature_ax.spines["right"].set_visible(True)
                    feature_ax.spines["right"].set_color(featurecolor[feature])
                    feature_ax.spines["right"].set_linewidth(0.5)
                    feature_ax.spines["right"].set_position(('outward',35 * spineindex))
                    feature_ax.yaxis.set_label_position("right")
                    feature_ax.yaxis.set_ticks_position('right')
                    spineindex += 1
                    
                else:
                    feature_ax=ax[feature]
                    feature_ax.plot(t_feature,events[i]["features"][feature]["raw"],linewidth=1.6,color=featurecolor[feature])
                    make_patch_spines_invisible(feature_ax)
                    feature_ax.spines["right"].set_color(featurecolor[feature])
                    feature_ax.yaxis.set_ticklabels([])
                    
                if showStatistics:
                    h_columns=t_audio[-1]/(len(events[i]["features"])-4)
                    x = h_columns*(featureindex +1)
                    y = events[i]["features"][feature]["mean"]
                    plotStatistics(feature,events[i],t_feature,featurecolor[feature],ax[feature],x,y,h_columns)
                
                featureindex += 1

        plt.axvline(x=markBegin,linewidth=1,color='r')
        if showNumbers:
            plt.text(markBegin+0.05, 0.05,'%i'% (i+1),bbox=dict(boxstyle='round', \
                facecolor='r', alpha=0.5),fontsize=14,horizontalalignment='left',transform=trans)
        
    lines, labels = ax1.get_legend_handles_labels()
    try:
        for feature in ax: 
            lines2, labels2 = ax[feature].get_legend_handles_labels()
            lines += lines2
            labels += labels2
        ax1.legend(lines, labels, loc=1)
    except NameError:
        ax1.legend(lines, labels, loc=1)
            
    wavPlayer(samples,samplerate)




