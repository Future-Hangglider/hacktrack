
import pandas, numpy
import scipy.stats
import cv2
import ipywidgets as widgets
from IPython.display import display
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
parameters =  cv2.aruco.DetectorParameters_create()

mtx = numpy.array([[9.90618474e+02, 0.00000000e+00, 6.53572956e+02],
        [0.00000000e+00, 1.00755969e+03, 3.67872669e+02],
        [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
dist = numpy.array([[-0.57453909,  0.42458431, -0.01814159, -0.00694322, -0.17175265]])

WframenumberR = widgets.IntRangeSlider(description="frame", value=(50, 100), min=0, max=200, continuous_update=False)
WframenumberR.layout.width = "600px"
Wledxselrange = widgets.IntRangeSlider(value=(100, 200), min=0, max=300, continuous_update=False)
Wledyselrange = widgets.IntRangeSlider(value=(200, 300), min=0, max=300, continuous_update=False)
uiledrg = widgets.HBox([Wledxselrange, Wledyselrange])
ui = widgets.VBox([WframenumberR, uiledrg])

def plotframewindow(cap, framenumberR, ledxselrange, ledyselrange):
    plt.figure(figsize=(17,6))
    framenumber = framenumberR[0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, framenumber)
    flag, frame = cap.retrieve()
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters, cameraMatrix=mtx, distCoeff=dist)
    frame = cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    plt.imshow(frame)
    plt.gca().add_patch(Rectangle((ledxselrange[0], ledyselrange[0]), ledxselrange[1]-ledxselrange[0], ledyselrange[1]-ledyselrange[0], linewidth=1, edgecolor='b', facecolor='none'))
    print("Meanred", frame[ledxselrange[0]:ledxselrange[1], ledyselrange[0]:ledyselrange[1], 0].mean())


def frameselectinteractive(cap):
    frameheight, framewidth = cap.get(cv2.CAP_PROP_FRAME_HEIGHT), cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    framecount = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    
    WframenumberR.min, WframenumberR.max = 1, framecount
    WframenumberR.value = (framecount//2, framecount)
    Wledxselrange.min, Wledxselrange.max = 0, framewidth
    Wledxselrange.value = (framewidth//3, 2*framewidth//3)
    Wledyselrange.min, Wledyselrange.max = 0, frameheight
    Wledyselrange.value = (2*frameheight//3, frameheight)
    
    params = {'framenumberR':WframenumberR, 'ledxselrange':Wledxselrange, 'ledyselrange':Wledyselrange, 
              'cap':widgets.fixed(cap)}
    outputfigure = widgets.interactive_output(plotframewindow, params)
    outputfigure.layout.height = '400px'
    display(ui, outputfigure);

def extractledflashframes(cap):
    framenumberR = WframenumberR.value
    print("scanning between frames", framenumberR)
    ledxselrange, ledyselrange = Wledxselrange.value, Wledyselrange.value
    
    vals = [ ]
    cap.set(cv2.CAP_PROP_POS_FRAMES, framenumberR[0]-1)
    while True:
        flag, frame = cap.read()   # advances then retrieves
        if not flag:                      break
        framenum = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if framenum > framenumberR[1]:   break
        if (framenum%1000) == 0:
            print(framenum)
        x = frame[ledyselrange[0]:ledyselrange[1], ledxselrange[0]:ledxselrange[1]]
        val = { "framenum":framenum, "b":x[:,:,0].mean(), "g":x[:,:,1].mean(), "r":x[:,:,2].mean() }   # BGR
        vals.append(val)
    ledbrights = pandas.DataFrame.from_dict(vals)
    ledbrights.set_index("framenum", inplace=True)
    ledbrights.index.name = None
    return ledbrights
    
    
#cap = cv2.VideoCapture(vidfile
#frameselectinteractive(cap)
# Then
#ledbrights = extractledflashframes(cap)


def framestotime(videoledonvalues, ledswitchtimes):
    # find ratios of subsequent on moments
    videoledonframes = videoledonvalues&(True^videoledonvalues.shift())
    videoledonframesI = videoledonvalues.index.to_series()[videoledonframes]
    videoledonframedurations = videoledonframesI.diff().iloc[1:]
    vr = (videoledonframedurations/videoledonframedurations.shift(1)).iloc[1:]

    ledontimes = ledswitchtimes.index.to_series()[ledswitchtimes]
    ledondurations = ledontimes.diff().iloc[1:]/pandas.Timedelta(seconds=1)
    lr = (ledondurations/ledondurations.shift(1)).iloc[1:]

    lrV = lr.values
    vrV = vr.values

    # overlap and find differences
    k = [ ] 
    for i in range(-(len(lrV)-1), len(vrV)):
        llrV = lrV[max(-i,0):len(lrV)+min(0,-i)]
        lvrV = vrV[max(0,i):len(vrV)+min(i,0)]
        assert len(llrV) == len(lvrV)
        s = sum(abs(llrV - lvrV))
        if len(llrV) >= 2:
            k.append((s/len(llrV), i, len(llrV)))

    s = min(k)
    i = s[1]

    # interpolate and re-align
    ledalignment = pandas.DataFrame(lr.iloc[max(-i,0):len(lrV)+min(0,-i)], columns=["ledondurationratios"])
    ledalignment["videoledondurationratiosV"] = vrV[max(0,i):len(vrV)+min(i,0)]
    ledalignment["videoledondurationratiosI"] = vr.index[max(0,i):len(vrV)+min(i,0)]

    #ledalignment.videoledondurationratiosI.values
    #plt.plot(ledalignment.videoledondurationratiosI.values)
    k = scipy.stats.linregress(ledalignment.videoledondurationratiosI.values, 
                               (ledalignment.index - ledalignment.index[0])/pandas.Timedelta(seconds=1))
    print("Framerate", 1/k.slope)
    return videoledonvalues.index.to_series()*pandas.Timedelta(seconds=k.slope) + pandas.Timedelta(seconds=k.intercept) + ledalignment.index[0]

