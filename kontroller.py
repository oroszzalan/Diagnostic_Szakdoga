import pygame
import DMEModule
import DSCModule
import EGSModule
import EPSModule

pygame.init()
dme = DMEModule.DME_Module()
eps = EPSModule.EPS_Module(dme, None)
dsc = DSCModule.DSC_Module(None, eps, dme)
egs = EGSModule.EGS_module(dme, dsc)
eps.DSC = dsc
dsc.EGS = egs




clock = pygame.time.Clock()

joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

idleRPM = 800
maxRPM = 6700
rumble_threshold = False
Igniton_on = False











def main():
    global joysticks


    if pygame.joystick.get_count() == 0:
        print("Joystick not connected, simulation cannot be started")

    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                
                joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
                print("Joystick connected, simulation can be started please press the \"View\" button on the controller")

            if event.type == pygame.JOYBUTTONDOWN and event.button == 6:
                print("Starting simulation")
                ignition()

            if event.type == pygame.JOYDEVICEREMOVED:
                print("Joystick not connected, simulation cannot be started")


def ignition():
    global Igniton_on
    global rumble_threshold
    dme.joystick = joysticks[0] if joysticks else None
    egs.joystick = joysticks[0] if joysticks else None
    dsc.joystick = joysticks[0] if joysticks else None
    eps.joystick = joysticks[0] if joysticks else None


    while True:
        print
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 7 and not Igniton_on:
                print("Ignition turned ON")
                Igniton_on = True

            elif event.type == pygame.JOYBUTTONDOWN and event.button == 7 and Igniton_on:
                print("Ignition turned OFF")
                Igniton_on = False

            if event.type == pygame.JOYBUTTONDOWN and event.button == 0 and Igniton_on:
                rumble_threshold = True
                print("Car started")
                car_started()

            if event.type == pygame.JOYBUTTONDOWN and event.button == 6:
                print("simulation stopped")
                return

        

        if Igniton_on:
            dme.DME_simulation()
            egs.EGS_Simulation()
            dsc.DSC_simulation()
            eps.EPS_simulation()

        clock.tick(30)


def car_started():
    

    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                dme.rpm = 0
                print("Car stopped")
                return
            

        #throttle on DME
        axisThrottle = dme.joystick.get_axis(5)
        throttle = (axisThrottle + 1.0) / 2.0
        throttle = max(0.0, min(1.0, throttle))

       


        targetRPM = idleRPM + throttle * (maxRPM - idleRPM)
        dme.rpm += (targetRPM - dme.rpm) * 0.1

        dme.DME_simulation()
        egs.EGS_Simulation()
        dsc.DSC_simulation()
        eps.EPS_simulation()

        rpm_ratio = ((dme.rpm - idleRPM)) / (maxRPM - idleRPM)
        rpm_ratio = max(0.0, min(0.5, rpm_ratio))

        if rumble_threshold:
            joysticks[0].rumble(rpm_ratio + 0.05, rpm_ratio + 0.05, 100)
        else:
            joysticks[0].stop_rumble()

        clock.tick(30)


if __name__ == "__main__":
    main()