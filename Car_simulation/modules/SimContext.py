from .DMEModule import DME_Module
from .DSCModule import DSC_Module
from .EGSModule import EGS_Module
from .EPSModule import EPS_Module

class SimContext:
    """
    Egyetlen helyen inicializálja az összes szimulációs modult,
    helyes sorrendben, utólagos patch (eps.DSC = dsc) nélkül.

    Használat:
        sim = SimContext()
        sim.set_joystick(joy)
        sim.tick(dt)

        speed = sim.dsc.vehicle_speed
        rpm   = sim.dme.rpm
    """

    def __init__(self):
        # DME elsőként — nincs függősége
        self.dme = DME_Module()

        # DSC, EGS, EPS egymásra hivatkoznak, ezért __new__ + késleltetett __init__
        # Így minden objektum létezik már mielőtt a másik megkapja a referenciát
        self.dsc = DSC_Module.__new__(DSC_Module)
        self.egs = EGS_Module.__new__(EGS_Module)
        self.eps = EPS_Module.__new__(EPS_Module)

        # Most már minden referencia él — inicializálás helyes sorrendben
        DSC_Module.__init__(self.dsc, EGS=self.egs, EPS=self.eps, DME=self.dme)
        EGS_Module.__init__(self.egs, DME=self.dme, DSC=self.dsc)
        EPS_Module.__init__(self.eps, DME=self.dme, DSC=self.dsc)

    # ----------------------------------------------------------
    def set_joystick(self, joy):
        """Egy helyen állítja be a joystickot minden modulban."""
        for mod in (self.dme, self.egs, self.dsc, self.eps):
            mod.joystick = joy

    # ----------------------------------------------------------
    def tick(self, dt: float):
        """
        Egy helyen hívja meg az összes szimulációs lépést,
        helyes sorrendben (DME → EGS → DSC → EPS).
        """
        self.dme.DME_simulation()
        self.egs.EGS_Simulation()
        self.dsc.DSC_simulation()
        self.eps.EPS_simulation()

    # ----------------------------------------------------------
    def modules(self):
        """Visszaadja az összes modult tuple-ként — pl. OBD2Gateway-hez."""
        return self.dme, self.dsc, self.egs, self.eps
