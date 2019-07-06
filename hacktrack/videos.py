
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
    
    WframenumberR.min, WframenumberR.max = 0, framecount-1
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
    print(framenumberR)
    ledxselrange, ledyselrange = Wledxselrange.value, Wledyselrange.value
    framenums = [ ]
    rmeans, gmeans, bmeans = [ ], [ ], [ ]
    framenum = framenumberR[0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, framenum)
    while framenum < framenumberR[1]:
        flag, frame = cap.read()
        x = frame[ledxselrange[0]:ledxselrange[1], ledyselrange[0]:ledyselrange[1]]
        framenums.append(framenum)
        rmeans.append(x[:,:,0].mean())
        gmeans.append(x[:,:,1].mean())
        bmeans.append(x[:,:,2].mean())
        if (framenum%1000) == 0:
            print(framenum)
        framenum = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    return pandas.DataFrame(data={"r":rmeans, "g":gmeans, "b":bmeans}, index=framenums)
    
def extractledflashframesF(cap):
    framenumberR = WframenumberR.value
    print(framenumberR)
    ledxselrange, ledyselrange = Wledxselrange.value, Wledyselrange.value
    
    vals = [ ]
    framenum = framenumberR[0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, framenum)
    while framenum < framenumberR[1]:
        flag, frame = cap.read()
        x = frame[ledxselrange[0]:ledxselrange[1], ledyselrange[0]:ledyselrange[1]]
        val = { "framenum":framenum, "r":x[:,:,0].mean(), "g":x[:,:,1].mean(), "b":x[:,:,2].mean() }
        
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters, cameraMatrix=mtx, distCoeff=dist)
        if ids is not None:
            for idd, corner in zip(ids, corners):
                val["fx%d"%idd[0]] = corner[0][:,0].mean()
                val["fy%d"%idd[0]] = corner[0][:,1].mean()
        vals.append(val)
        
        if (framenum%1000) == 0:
            print(framenum)
        framenum = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    ledbrights = pandas.DataFrame.from_dict(vals)
    ledbrights.set_index("framenum", inplace=True)
    ledbrights.index.name = None
    return ledbrights
    
    
#cap = cv2.VideoCapture(vidfile
#frameselectinteractive(cap)
# Then
#ledbrights = extractledflashframes(cap)


def framestotime(videoledonvalues, ledswitchtimes):
    videoledonframes = videoledonvalues&(True^videoledonvalues.shift())
    videoledonframesI = videoledonvalues.index.to_series()[videoledonframes]
    videoledonframedurations = videoledonframesI.diff().iloc[1:]
    videoledondurationratios = (videoledonframedurations/videoledonframedurations.shift(1)).iloc[1:]

    ledontimes = ledswitchtimes.index.to_series()[ledswitchtimes]
    ledondurations = ledontimes.diff().iloc[1:]/pandas.Timedelta(seconds=1)
    ledondurationratios = (ledondurations/ledondurations.shift(1)).iloc[1:]

    ledondurationratiosV = ledondurationratios.values
    videoledondurationratiosV = videoledondurationratios.values

    #videoledondurationratiosV = videoledondurationratiosV[-61:]
    k = [ ]
    for i in range(len(ledondurationratiosV) - len(videoledondurationratiosV)):
        s = sum(abs(ledondurationratiosV[i:i+len(videoledondurationratiosV)] - videoledondurationratiosV))
        k.append((s, i))
    s = min(k)
    
    i = s[1]
    ledalignment = pandas.DataFrame(ledondurationratios.iloc[i:i+len(videoledondurationratios)], columns=["ledondurationratios"])
    #videoledondurationratios
    ledalignment["videoledondurationratiosV"] = videoledondurationratiosV
    ledalignment["videoledondurationratiosI"] = videoledondurationratios.index

    #ledalignment.videoledondurationratiosI.values
    #plt.plot(ledalignment.videoledondurationratiosI.values)
    k = scipy.stats.linregress(ledalignment.videoledondurationratiosI.values, 
                               (ledalignment.index - ledalignment.index[0])/pandas.Timedelta(seconds=1))
    print("Framerate", 1/k.slope)
    return videoledonvalues.index.to_series()*pandas.Timedelta(seconds=k.slope) + pandas.Timedelta(seconds=k.intercept) + ledalignment.index[0]

