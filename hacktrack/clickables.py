
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
    
outputfigure = None
t0t1Label = None
def plotfigure(t0s, dts, colos, figureheight, velwhisker, headingwhisker, wx, wy, fd):
    if outputfigure:  outputfigure.layout.height = figureheight

    t0 = pandas.Timestamp(t0s*3600*1e9 + fd.timestampmidnight.value)
    t1 = pandas.Timedelta(dts*60*1e9) + t0
    t0t1Label.value = "%s %s-%s" % (t0.isoformat()[:10], t0.isoformat()[11:19], t1.isoformat()[11:19])
    fd.t0, fd.t1 = t0, t1
    plt.figure(figsize=(8,8))
    pQ = fd.pQ[t0:t1]

    plt.gca().xaxis.tick_top()
    
    # timewise plot
    if colos == "TZ":  
        fd.LoadC("F")
        baro = fd.pF[fd.t0:fd.t1].Pr
        balt = utils.BaroToAltComplete(baro, pQ.alt, gpsoffset=None, plt=None)
        plt.plot(pQ.alt, label="GPS altitude")
        plt.plot(balt, label="barometric alt")
        plt.legend()
        plt.show()
        return
    
    # xy plots
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
        fd.LoadC("F")
        baro = fd.pF[fd.t0-pandas.Timedelta(seconds=30):fd.t1+pandas.Timedelta(seconds=30)].Pr
        timestep = numpy.mean((baro.index[1:]-baro.index[:-1]).astype(int)*1e-9)
        fbaro = utils.FiltFiltButter(baro, f=0.01, n=3)
        vario = fbaro.diff()*(-0.09/timestep)
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

    hcolcb = widgets.Checkbox(description="Colour by height", value=False)
    coloptions = widgets.Dropdown(options=['XY', 'altitude', 'velocity', 'vario', 'YZ', 'TZ'])
    velwhisker = widgets.IntSlider(min=0, max=5, description="velocity whiskers", continuous_update=False)
    headingwhisker = widgets.IntSlider(min=0, max=5, description="heading whiskers", continuous_update=False)

    windxslider = widgets.FloatSlider(description="windx", step=0.01, min=-10, max=10, start=0, continuous_update=False)
    windyslider = widgets.FloatSlider(description="windy", step=0.01, min=-10, max=10, start=0, continuous_update=False)

    uipaneleft = widgets.VBox([t0slider, dtslider, t0t1Label, figureheightSelection])
    uipaneright = widgets.VBox([hcolcb, coloptions, velwhisker, headingwhisker])
    uipanefarright = widgets.VBox([windxslider, windyslider])
    ui = widgets.HBox([uipaneleft, uipaneright, uipanefarright])

    params = {'t0s': t0slider, 'dts': dtslider, 
              "velwhisker":velwhisker, "headingwhisker":headingwhisker, 
              "colos":coloptions, 
              "figureheight":figureheightSelection, 
              "wx":windxslider, "wy":windyslider, 
              'fd':widgets.fixed(fd) }
    outputfigure = widgets.interactive_output(plotfigure, params)
    outputfigure.layout.height = '400px'
    display(ui, outputfigure);
