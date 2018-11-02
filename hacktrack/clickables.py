
# handy interactive things
#from ipywidgets import interact, Layout, interactive, fixed, interact_manual
#idgets import interact, interactive, fixed, interact_manual
import pandas, numpy
import ipywidgets as widgets
from IPython.display import display
from matplotlib.collections import LineCollection
from matplotlib import pyplot as plt
from . import utils


def plotvalcolour(pQx, pQy, pval):
    points = numpy.array([pQx, pQy]).T.reshape(-1, 1, 2)
    segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=plt.get_cmap('cool'), norm=plt.Normalize(min(pval), max(pval)))
    lc.set_array(pval)
    cs = plt.gca().add_collection(lc)
    plt.xlim(min(pQx), max(pQx))  # why is this necessary to set the dimensions?
    plt.ylim(min(pQy), max(pQy))
    plt.colorbar(cs)

def plotwhiskers(pQx, pQy, vel, deg, velfac, col):
    spQx = pQx.iloc[::int(len(pQx)/500+1)]
    spQy = pQy.iloc[::int(len(pQy)/500+1)]
    svel = utils.InterpT(spQx, vel)
    if col == "green":
        svel = -(40-svel)*(velfac/4)
    else:
        svel = svel*velfac
    sdeg = utils.InterpT(spQx, deg)
    srad = numpy.radians(sdeg)
    svx = numpy.sin(srad)*svel
    svy = numpy.cos(srad)*svel
    segments = numpy.array([spQx, spQy, spQx+svx, spQy+svy]).T.reshape(-1,2,2)
    lc = LineCollection(segments, color=col)
    plt.gca().add_collection(lc)
    
def CalcVario(fd):
    fd.LoadC("F")
    baro = fd.pF[fd.t0-pandas.Timedelta(seconds=30):fd.t1+pandas.Timedelta(seconds=30)].Pr
    timestep = numpy.mean((baro.index[1:]-baro.index[:-1]).astype(int)*1e-9)
    fbaro = utils.FiltFiltButter(baro, f=0.01, n=3)
    vario = fbaro.diff()*(-0.09/timestep)
    return vario.dropna()

    
outputfigure = None
t0t1Label = None

def rescaletsval(val, brescale, lo=None, hi=None):
    if not brescale:
        return val
    if lo is None:
        lo, hi = min(val), max(val)
    return (val - (hi+lo)/2)*(2/(hi-lo))


def plottimeseries(bZalt, hangspottimeslider, cbvario, cbaccellerations, cborientations, cbhangspot, fd):
    plt.figure(figsize=(13,8))

    if bZalt:
        pQ = fd.pQ[fd.t0:fd.t1]
        if fd.bIGConly:
            plt.plot(pQ.altb, label="barometric alt")  # pQ === pIGC
            plt.plot(pQ.alt, label="gps alt")
        else:
            fd.LoadC("F")
            baro = fd.pF[fd.t0:fd.t1].Pr
            if len(fd.pQ):
                balt = utils.BaroToAltComplete(baro, pQ.alt, gpsoffset=None, plt=None)
                plt.plot(pQ.alt, label="GPS altitude")
            else:
                balt = (102726 - baro)*0.037867
            plt.plot(balt, label="barometric alt")
            if hasattr(fd, "aF"):
                aQ = fd.aQ[fd.t0:fd.t1]
                baroA = fd.pF[fd.t0:fd.t1].Pr
                if len(fd.pQ):
                    baltA = utils.BaroToAltComplete(baroA, aQ.alt, gpsoffset=None, plt=None)
                    plt.plot(aQ.alt, label="GPSA altitude")
                else:
                    baltA = (102726 - baro)*0.037867
                plt.plot(baltA, label="barometricA alt")
        plt.gca().xaxis.tick_top()
        plt.legend()
        plt.show()
        return
    
    cbcount = cbvario + cbaccellerations + cborientations + cbhangspot
    if cbcount == 0:
        cbvario = True
    brescale = (cbcount >= 2)  # more than one value; so scale them all
    if cbvario:
        vario = CalcVario(fd)
        vario = rescaletsval(vario, brescale)
        plt.plot(vario, label="Vario")
        
    if cbaccellerations or cborientations:
        fd.LoadC("Z")
        pZ = fd.pZ[fd.t0:fd.t1]
        if cbaccellerations:
            lo, hi = min(min(pZ.ax), min(pZ.ay), min(pZ.az)), max(max(pZ.ax), max(pZ.ay), max(pZ.az))
            plt.plot(rescaletsval(pZ.ax, brescale, lo, hi))
            plt.plot(rescaletsval(pZ.ay, brescale, lo, hi))
            plt.plot(rescaletsval(pZ.az, brescale, lo, hi))
        if cborientations:
            lo, hi = min(min(pZ.pitch), min(pZ.roll)), max(max(pZ.pitch), max(pZ.roll))
            plt.plot(rescaletsval(pZ.pitch, brescale, lo, hi))
            plt.plot(rescaletsval(pZ.roll, brescale, lo, hi))
            plt.plot(rescaletsval(pZ.heading, brescale))

    if cbhangspot:
        td = pandas.Timedelta(seconds=hangspottimeslider)
        fy = fd.fy[fd.t0-td:fd.t1-td]
        lo, hi = min(min(fy.x), min(fy.y)), max(max(fy.x), max(fy.y))
        fyx = rescaletsval(fy.x, brescale)
        fyy = rescaletsval(fy.y, brescale)
        plt.plot(fy.index+td, fyx, label="hangspotx")
        plt.plot(fy.index+td, fyy, label="hangspoty")

    plt.gca().xaxis.tick_top()
    plt.legend()
    plt.show()


    
def plotfigure(t0s, dts, colos, figureheight, velwhisker, headingwhisker, wx, wy, 
               hangspottimeslider, cbvario, cbaccellerations, cborientations, cbhangspot, 
               fd):
    if outputfigure:
        outputfigure.layout.height = figureheight

    t0 = pandas.Timestamp(t0s*3600*1e9 + fd.timestampmidnight.value)
    t1 = pandas.Timedelta(dts*60*1e9) + t0
    t0t1Label.value = "%s %s-%s" % (t0.isoformat()[:10], t0.isoformat()[11:19], t1.isoformat()[11:19])
    fd.t0, fd.t1 = t0, t1

    
    # timewise plots
    if colos[:1] == "T":
        plottimeseries((colos == "TZ"), hangspottimeslider, cbvario, cbaccellerations, cborientations, cbhangspot, fd)
        return
    
    # xy plots
    plt.figure(figsize=(8,8))
    plt.gca().xaxis.tick_top()

    pQ = fd.pQ[fd.t0:fd.t1]
    if wx == 0 and wy == 0:
        pQx, pQy = pQ.x, pQ.y
    else:  # wind added
        ts = (pQ.index - fd.t0).astype(int)*1e-9
        pQx, pQy = pQ.x - ts*wx, pQ.y - ts*wy
    
    plt.subplot(111, aspect="equal")
    if colos == "altitude":
        plotvalcolour(pQx, pQy, pQ.alt)
        plt.scatter(pQx.iloc[-2:], pQy.iloc[-2:])
        
    elif colos == "velocity":
        # warning, velocity not changed by wind vector
        velmag = utils.InterpT(pQ, fd.pV.vel)
        if wx != 0 or wy != 0:
            veldeg = utils.InterpT(pQ, fd.pV.deg)
            velrad = numpy.radians(veldeg)
            velvx = numpy.sin(velrad)*velmag
            velvy = numpy.cos(velrad)*velmag
            velmag = numpy.hypot(velvx - wx, velvy - wy)
        plotvalcolour(pQx, pQy, velmag)
        plt.scatter(pQx.iloc[-2:], pQy.iloc[-2:])
    
    elif colos == "vario":    
        # heavily filter so we can use adjacent samples
        vario = CalcVario(fd)
        varioQ = utils.InterpT(pQ, vario)
        plotvalcolour(pQx, pQy, varioQ)
        plt.scatter(pQx.iloc[-2:], pQy.iloc[-2:])
        
    elif colos == "YZ":
        plt.plot(pQy, pQ.alt)
        plt.scatter(pQy.iloc[-5:], pQ.alt.iloc[-5:])
    else:  # XY case
        plt.plot(pQx, pQy)
        plt.scatter(pQx.iloc[-5:], pQy.iloc[-5:])
    
    if velwhisker != 0:
        # warning, velocity not changed by wind vector
        plotwhiskers(pQx, pQy, fd.pV.vel, fd.pV.deg, velwhisker, "pink")
    if headingwhisker != 0:
        fd.LoadC("Z")
        plotwhiskers(pQx, pQy, fd.pZ.pitch, fd.pZ.heading, headingwhisker, "green")
    
    plt.show()

    
def plotinteractivegpstrack(fd):
    global outputfigure, t0t1Label
    t0hour = (fd.ft0-fd.timestampmidnight).value/1e9/3600
    t1hour = (fd.ft1-fd.timestampmidnight).value/1e9/3600
    dtminutes = (fd.ft1 - fd.ft0).value/1e9/60

    t0t1Label = widgets.Label(value="t0")
    t0t1Label.layout.width = "300px"
    t0slider = widgets.FloatSlider(description="starthour", step=1/3600, min=t0hour, max=t1hour, continuous_update=False)
    dtslider = widgets.FloatSlider(description="minutes", value=3, step=1/60, max=dtminutes, continuous_update=False)
    figureheightSelection = widgets.SelectionSlider(options=['300px', '400px', '500px', '600px', '800px'], value='400px', description='display height', continuous_update=False)

    coloptions = widgets.Dropdown(options=['Tseries', 'TZ', 'XY', 'altitude', 'velocity', 'vario', 'YZ'])

    cbvario = widgets.Checkbox(description="vario", value=False)
    cbaccellerations = widgets.Checkbox(description="accel", value=False)
    cborientations = widgets.Checkbox(description="orient", value=False)
    cbhangspot = widgets.Checkbox(description="hangspot", value=False)

    #cbaccellerations.layout.width = cbvario.layout.width = "60px"  # causes overlaps and doesn't work.  needs more looking at

    hangspottimeslider = widgets.FloatSlider(description="hangspot_t", step=0.01, min=-10, max=10, start=0, continuous_update=False)

    velwhisker = widgets.IntSlider(min=0, max=5, description="velocity whiskers", continuous_update=False)
    headingwhisker = widgets.IntSlider(min=0, max=5, description="heading whiskers", continuous_update=False)

    windxslider = widgets.FloatSlider(description="windx", step=0.01, min=-10, max=10, start=0, continuous_update=False)
    windyslider = widgets.FloatSlider(description="windy", step=0.01, min=-10, max=10, start=0, continuous_update=False)

    # build up the panels of components
    uipaneleft = widgets.VBox([t0slider, dtslider, t0t1Label, figureheightSelection])
    
    uicboxes = widgets.HBox([cbvario, cbaccellerations])
    uipaneright = widgets.VBox([uicboxes, coloptions, velwhisker, headingwhisker])
    
    uicboxes2 = widgets.HBox([cborientations, cbhangspot])
    uipanefarright = widgets.VBox([windxslider, windyslider, uicboxes2, hangspottimeslider])
    
    ui = widgets.HBox([uipaneleft, uipaneright, uipanefarright])

    params = {'t0s': t0slider, 'dts': dtslider, 
              "velwhisker":velwhisker, "headingwhisker":headingwhisker, 
              "colos":coloptions, 
              "figureheight":figureheightSelection, 
              "wx":windxslider, "wy":windyslider, "hangspottimeslider":hangspottimeslider, 
              "cbvario":cbvario, "cbaccellerations":cbaccellerations, "cborientations":cborientations, "cbhangspot":cbhangspot, 
              'fd':widgets.fixed(fd) }
    outputfigure = widgets.interactive_output(plotfigure, params)
    outputfigure.layout.height = '400px'
    display(ui, outputfigure);
    
