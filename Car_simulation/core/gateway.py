from modules.OBD2 import OBD2Gateway

def make_gateway(sim):
    dme, dsc, egs, eps = sim.modules()
    gw = OBD2Gateway(port="COM8", dme=dme, dsc=dsc, egs=egs, eps=eps, baudrate=38400)
    gw.start()
    return gw