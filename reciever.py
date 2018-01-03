import zmq, time, threading
from signalslot import Signal, SlotMustAcceptKeywords, Slot
import signal
import sys
import time

def sigterm_handler(signal, frame):
    global gui
    # save the state here or do whatever you want
    print('booyah! bye bye')
    gui.plot_closed()
    sys.exit(0)

class zmqReceiverLogger():
    def __init__(self, *args, **kwargs):
        # super(zmqReceiverLogger,self).__init__()
        self.thread = zmqReceiverLoggerThread(*args, **kwargs)
        self.thread.start()

class zmqReceiverLoggerThread(threading.Thread):

    data_received = Signal(args=[], threadsafe=True)

    def __init__(self, port=5556):
        super(zmqReceiverLoggerThread, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.port = port
        self.interrupt = False

    def run(self):
        self.socket.bind("tcp://*:%s" % (self.port))

        while True:
            try:
                data = self.socket.recv_pyobj()
                if len(data) > 0:
                    print data
                    self.data_received.emit(args=data)
            except (KeyboardInterrupt, SystemExit):
                self.socket.close()
                self.context.term()
            else:
                pass

from numpy import exp, linspace, meshgrid
from traits.api import HasTraits, Instance
from traitsui.api import Item, View
from chaco.api import ArrayPlotData, Plot, jet
from enable.api import ComponentEditor
import collections

class ImagePlot(HasTraits):
    plot = Instance(Plot)
    receiver = zmqReceiverLogger()

    signal.signal(signal.SIGINT, sigterm_handler)

    def __init__(self, port=5556):
        super(ImagePlot, self).__init__()
        self.slot_a = Slot(self.slot)
        self.x = range(100)
        self.y = collections.deque(maxlen=100)
        self.plotdata = ArrayPlotData(x=self.x, y=self.y)
        self.receiver.thread.data_received.connect(self.slot_a)

    def slot(self, **kwargs):
        print kwargs['args'][0]
        self.update_plot(kwargs['args'][0])

    traits_view = View(
        Item('plot', editor=ComponentEditor(), show_label=False),
        width=500, height=500, resizable=True, title="Chaco Plot")

    def update_plot(self, data):
        self.y.append(data[1])
        self.plotdata.set_data("x", self.x)
        self.plotdata.set_data("y", self.y)

    def _plot_default(self):
        plot = Plot(self.plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        plot.title = "Position of Laser centroid"
        return plot

    def plot_closed(self):
        print 'Close called!'
        self.receiver.thread.socket.close()
        self.receiver.thread.context.term()
        sys.exit(0)

if __name__ == "__main__":
    global gui
    gui = ImagePlot()
    gui.configure_traits()
