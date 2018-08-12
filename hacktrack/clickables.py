
# handy interactive things
#from ipywidgets import interact, Layout, interactive, fixed, interact_manual
#idgets import interact, interactive, fixed, interact_manual
import pandas, numpy
import ipywidgets as widgets
from IPython.display import display
from matplotlib.collections import LineCollection
from matplotlib import pyplot as plt
from . import utils

def plotvalcolour(pQ, pval):
    points = numpy.array([pQ.x, pQ.y]).T.reshape(-1, 1, 2)
    segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=plt.get_cmap('cool'), norm=plt.Normalize(min(pval), max(pval)))
    lc.set_array(pval)
    cs = plt.gca().add_collection(lc)
    plt.xlim(min(pQ.x), max(pQ.x))  # why is this necessary to set the dimensions?
    plt.ylim(min(pQ.y), max(pQ.y))
    plt.colorbar(cs)

    
outputfigure = None
t0t1Label = None
def plotfigure(t0s, dts, colos, figureheight, fd):
    if outputfigure:  outputfigure.layout.height = figureheight

    t0 = pandas.Timestamp(t0s*3600*1e9 + fd.timestampmidnight.value)
    t1 = pandas.Timedelta(dts*60*1e9) + t0
    t0t1Label.value = "%s %s-%s" % (t0.isoformat()[:10], t0.isoformat()[11:19], t1.isoformat()[11:19])
    fd.t0, fd.t1 = t0, t1
    plt.figure(figsize=(8,8))
    pQ = fd.pQ[t0:t1]
    pQ5 = pQ.iloc[-5:]
    if colos != "TZ":
        plt.subplot(111, aspect="equal")

    if colos == "altitude":
        plotvalcolour(pQ, pQ.alt)
    elif colos == "velocity":
        plotvalcolour(pQ, utils.InterpT(pQ, fd.pV.vel))
    elif colos == "YZ":
        plt.plot(pQ.y, pQ.alt)
        plt.scatter(pQ5.x, pQ5.alt)
    elif colos == "TZ":
        plt.plot(pQ.alt)
    else:
        plt.plot(pQ.x, pQ.y)
        plt.scatter(pQ5.x, pQ5.y)
    plt.gca().xaxis.tick_top()
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
    hcolcb = widgets.Checkbox(description="Colour by height", value=False)
    coloptions = widgets.Dropdown(options=['none', 'altitude', 'velocity', 'YZ', 'TZ'])
    figureheightSelection = widgets.SelectionSlider(options=['300px', '400px', '500px', '600px', '800px'], value='400px', description='display height', continuous_update=False)

    uipaneleft = widgets.VBox([t0slider, dtslider, t0t1Label, figureheightSelection])
    uipaneright = widgets.VBox([hcolcb, coloptions])
    ui = widgets.HBox([uipaneleft, uipaneright])

    params = {'t0s': t0slider, 'dts': dtslider, "colos":coloptions, 
              "figureheight":figureheightSelection, 
              'fd':widgets.fixed(fd) }
    outputfigure = widgets.interactive_output(plotfigure, params)
    outputfigure.layout.height = '400px'
    display(ui, outputfigure);

