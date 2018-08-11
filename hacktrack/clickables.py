
# handy interactive things
#from ipywidgets import interact, Layout, interactive, fixed, interact_manual
#idgets import interact, interactive, fixed, interact_manual
import pandas, numpy
import ipywidgets as widgets
from IPython.display import display
from matplotlib.collections import LineCollection
from matplotlib import pyplot as plt

def plotaltitudecolour(pQ):
    points = numpy.array([pQ.x, pQ.y]).T.reshape(-1, 1, 2)
    segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=plt.get_cmap('cool'), norm=plt.Normalize(min(pQ.alt), max(pQ.alt)))
    lc.set_array(pQ.alt)
    cs = plt.gca().add_collection(lc)
    plt.xlim(min(pQ.x), max(pQ.x))
    plt.ylim(min(pQ.y), max(pQ.y))
    plt.colorbar(cs)
    plt.show()
    

def plotinteractivegpstrack(fd):
    t0hour = (fd.ft0-fd.timestampmidnight).value/1e9/3600
    t1hour = (fd.ft1-fd.timestampmidnight).value/1e9/3600
    dtminutes = (fd.ft1 - fd.ft0).value/1e9/60

    t0t1Label = widgets.Label(value="t0")
    t0t1Label.layout.width = "300px"
    t0slider = widgets.FloatSlider(description="starthour", step=1/3600, min=t0hour, max=t1hour, continuous_update=False)
    dtslider = widgets.FloatSlider(description="minutes", value=3, step=1/60, max=dtminutes, continuous_update=False)
    hcolcb = widgets.Checkbox(description="Colour by height", value=False)
    coloptions = widgets.Dropdown(options=['none', 'altitude', 'velocity', 'YZ', 'TZ'])

    uipaneleft = widgets.VBox([t0slider, dtslider, t0t1Label])
    uipaneright = widgets.VBox([hcolcb, coloptions])
    ui = widgets.HBox([uipaneleft, uipaneright])
    def plotfigure(t0s, dts, colos):
        t0 = pandas.Timestamp(t0s*3600*1e9 + fd.timestampmidnight.value)
        t1 = pandas.Timedelta(dts*60*1e9) + t0
        t0t1Label.value = "%s %s-%s" % (t0.isoformat()[:10], t0.isoformat()[11:19], t1.isoformat()[11:19])
        fd.t0, fd.t1 = t0, t1
        plt.figure(figsize=(8,8))
        pQ = fd.pQ[t0:t1]
        pQ5 = pQ.iloc[-5:]
        if colos == "altitude":
            plt.subplot(111, aspect="equal")
            plotaltitudecolour(pQ)
        elif colos == "YZ":
            plt.subplot(111, aspect="equal")
            plt.plot(pQ.y, pQ.alt)
            plt.scatter(pQ5.x, pQ5.alt)
        elif colos == "TZ":
            plt.plot(pQ.alt)
        else:
            plt.subplot(111, aspect="equal")
            plt.plot(pQ.x, pQ.y)
            plt.scatter(pQ5.x, pQ5.y)
        plt.show()

    out = widgets.interactive_output(plotfigure, {'t0s': t0slider, 'dts': dtslider, "colos":coloptions})
    out.layout.height = '450px'
    display(out, ui);
