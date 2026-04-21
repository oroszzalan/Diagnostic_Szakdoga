import time
import pygame

from modules.SimContext import SimContext
from config import WIDTH, HEIGHT, FPS, IDLE_RPM, MAX_RPM
from config import BTN_IGNITION, BTN_ENGINE, BTN_DTC_INJECT, BTN_DTC_CLEAR
from core.helpers import clamp, lerp
from core.dtc.inject import inject_all_modules, clear_all_modules, count_active_dtcs, count_stored_dtcs
from core.input import read_trigger_axis
from core.gateway import make_gateway
from graphics.background import draw_background
from graphics.gauges import draw_speedometer, draw_tachometer, draw_small_gauge
from graphics.center_panel import draw_center_panel
from graphics.indicators import draw_dtc_indicator
from graphics.colors import ORANGE, GREEN, TEXT_DIM
from graphics.text import draw_text
from ui.fonts import create_fonts

class ClusterApp:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BMW F90 M5 Cluster")
        self.clock = pygame.time.Clock()
        self.fonts = create_fonts()

        self.sim = SimContext()
        self.obd2 = make_gateway(self.sim)

        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for j in self.joysticks:
            j.init()

        self.ignition_on = False
        self.prev_ignition_on = False
        self.engine_running = False
        self.rumble_enabled = True

        self.dtc_msg = ""
        self.dtc_msg_until = 0.0

    def refresh_joysticks(self):
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for j in self.joysticks:
            j.init()

    def handle_events(self, now):
        running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYDEVICEADDED:
                self.refresh_joysticks()

            elif event.type == pygame.JOYDEVICEREMOVED:
                self.refresh_joysticks()

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BTN_IGNITION:
                    self.ignition_on = not self.ignition_on
                    if not self.ignition_on:
                        self.engine_running = False
                        self.sim.dme.rpm = 0

                elif event.button == BTN_ENGINE and self.ignition_on:
                    self.engine_running = not self.engine_running
                    if not self.engine_running:
                        self.sim.dme.rpm = 0

                elif event.button == BTN_DTC_INJECT:
                    injected = inject_all_modules(self.sim, count=2)
                    if injected:
                        self.dtc_msg = "DTC: " + ", ".join(injected[:6])
                        if len(injected) > 6:
                            self.dtc_msg += f" (+{len(injected)-6})"
                        self.dtc_msg_until = now + 5.0

                elif event.button == BTN_DTC_CLEAR:
                    clear_all_modules(self.sim)
                    self.dtc_msg = "Összes DTC törölve (DME / DSC / EGS / EPS)"
                    self.dtc_msg_until = now + 3.0

        return running

    def update_gateway_state(self):
        if self.ignition_on and not self.prev_ignition_on:
            if not self.obd2.running:
                self.obd2 = make_gateway(self.sim)
        elif not self.ignition_on and self.prev_ignition_on:
            self.obd2.close()
        self.prev_ignition_on = self.ignition_on

    def update_simulation(self, dt):
        joy = self.joysticks[0] if self.joysticks else None
        self.sim.set_joystick(joy)

        throttle = read_trigger_axis(joy, 5)
        brake = read_trigger_axis(joy, 4)

        if self.ignition_on:
            if self.engine_running:
                target_rpm = IDLE_RPM + throttle * (MAX_RPM - IDLE_RPM)
                self.sim.dme.rpm += (target_rpm - self.sim.dme.rpm) * min(1.0, 6.0 * dt)
            else:
                self.sim.dme.rpm += (0 - self.sim.dme.rpm) * min(1.0, 8.0 * dt)
                if self.sim.dme.rpm < 5:
                    self.sim.dme.rpm = 0

            if joy is not None:
                self.sim.tick(dt)
            else:
                self.sim.dme.throttlePosition = 0.0
                self.sim.dme.DME_simulation()
                self.sim.egs.EGS_Simulation()
                self.sim.dsc.brakePosition = brake * 100.0
                self.sim.dsc.DSC_simulation()
                self.sim.eps.EPS_simulation()
        else:
            self.sim.dme.rpm = 0

        self.update_rumble(joy)

    def update_rumble(self, joy):
        if joy is not None and self.rumble_enabled and self.engine_running:
            rpm_ratio = clamp((self.sim.dme.rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM), 0.0, 0.5)
            try:
                joy.rumble(rpm_ratio + 0.05, rpm_ratio + 0.05, 80)
            except Exception:
                pass
        elif joy is not None:
            try:
                joy.stop_rumble()
            except Exception:
                pass

    def draw(self, now):
        screen = self.screen
        font_huge, font_big, font_mid, font_small, font_tiny, font_micro = self.fonts

        speed = clamp(self.sim.dsc.vehicle_speed, 0.0, 330.0)
        rpm_k = clamp(self.sim.dme.rpm / 1000.0, 0.0, 8.0)

        fuel_ratio = self.sim.dme.fuelLevelLiters / self.sim.dme.fuelTankLiters
        fuel_value = lerp(0.71, 0.41, fuel_ratio)

        temp = self.sim.dme.coolantTemp
        tn = ((temp - 70) / 30 * 0.5) if temp <= 100 else (0.5 + (temp - 100) / 70 * 0.5)
        temp_value = lerp(0.71, 0.41, clamp(tn, 0.0, 1.0))

        active_dtc = count_active_dtcs(self.sim)
        stored_dtc = count_stored_dtcs(self.sim)

        draw_background(screen)
        draw_speedometer(screen, (370, 280), 232, speed, font_small, font_tiny, font_big)
        draw_tachometer(screen, (1030, 280), 232, rpm_k, font_small, font_tiny, font_big)
        draw_small_gauge(screen, (210, 490), 88, fuel_value, 0.41, 0.71, "F", "1/2", "E", "km", True, font_tiny)
        draw_small_gauge(screen, (1190, 490), 88, temp_value, 0.41, 0.71, "170", "100", "70", "°C", False, font_tiny)

        draw_center_panel(
            screen, self.fonts,
            gear=self.sim.egs.GearSelector,
            vehicle_speed=self.sim.dsc.vehicle_speed,
            coolant_temp=self.sim.dme.coolantTemp,
            abs_active=self.sim.dsc.absActive,
            tc_active=self.sim.dsc.tractionControlActive,
            sc_active=self.sim.dsc.stabilityControlActive,
            steering_angle=getattr(self.sim.eps, "steeringAngle", 0.0),
            torque=self.sim.dme.Torque,
            horsepower=self.sim.dme.HorsePower,
            ignition_on=self.ignition_on,
            engine_running=self.engine_running,
            active_dtc_count=active_dtc,
        )

        draw_dtc_indicator(screen, font_micro, active_dtc, stored_dtc)

        if now < self.dtc_msg_until and self.dtc_msg:
            col = ORANGE if "DTC:" in self.dtc_msg else GREEN
            draw_text(screen, self.dtc_msg, font_micro, col, (WIDTH // 2, HEIGHT - 35))

        draw_text(
            screen,
            "menu=gyújtás | A=motor | Y=DTC inject | X=DTC törlés",
            font_micro, TEXT_DIM, (WIDTH // 2, HEIGHT - 18)
        )

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            now = time.time()

            running = self.handle_events(now)
            self.update_gateway_state()
            self.update_simulation(dt)
            self.draw(now)

        self.obd2.close()
        pygame.quit()