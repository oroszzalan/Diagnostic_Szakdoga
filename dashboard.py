import math
import time
import random
import pygame

import DMEModule
import DSCModule
import EGSModule
import EPSModule

from OBD2 import OBD2Gateway

# =========================
# CONFIG
# =========================
WIDTH, HEIGHT = 1400, 650
FPS = 60

BG = (0, 0, 0)
WHITE = (242, 245, 250)
TEXT = (220, 224, 232)
TEXT_DIM = (145, 150, 162)
TEXT_FAINT = (95, 100, 112)

RING = (205, 210, 220)
RING_DIM = (88, 94, 106)

RED = (210, 28, 28)
RED_BRIGHT = (255, 72, 72)
BLUE_SOFT = (70, 95, 145)
YELLOW = (255, 210, 90)
GREEN = (80, 200, 80)
ORANGE = (255, 160, 0)

M_BLUE1 = (92, 186, 255)
M_BLUE2 = (52, 120, 230)
M_RED = (220, 45, 55)

IDLE_RPM = 800
MAX_RPM  = 6700

# Kontroller gomb kiosztás
BTN_IGNITION   = 7   # menu
BTN_ENGINE     = 0   # A
BTN_DTC_INJECT = 3   # Y — random DTC injektálás minden modulba
BTN_DTC_CLEAR  = 2   # X — minden modul DTC törlése


# =========================
# DTC INJECT / CLEAR HELPERS
# =========================
def inject_all_modules(dme, dsc, egs, eps, count=2):
    """
    Minden modulba random DTC-ket injektál.
    count: max hány kód modulonként (minimum 1 garantált).
    Visszaadja az összes injektált kód listáját.
    """
    all_injected = []
    # Véletlenszerűen válasszuk ki hogy melyik modulba kerüljön hiba
    # (nem kötelező minden modulba minden alkalommal)
    modules = [dme, dsc, egs, eps]
    # 2-4 modult érintünk véletlenszerűen
    affected = random.sample(modules, k=random.randint(2, len(modules)))
    for mod in affected:
        injected = mod.inject_random_faults(count=count)
        all_injected.extend(injected)
    return all_injected


#DTC törlés
def clear_all_modules(dme, dsc, egs, eps):
    """Minden modul összes DTC-jét törli."""
    for mod in [dme, dsc, egs, eps]:
        mod.clear_all_faults()

#aktiv
def count_active_dtcs(dme, dsc, egs, eps):
    return (len(dme.activeDTC) + len(dsc.activeDTC) +
            len(egs.activeDTC) + len(eps.activeDTC))

#tárolt
def count_stored_dtcs(dme, dsc, egs, eps):
    return (len(dme.storedDTC) + len(dsc.storedDTC) +
            len(egs.storedDTC) + len(eps.storedDTC))


# =========================
# DRAW HELPERS
# =========================

#lineáris interpolárcíó köztes intervallum arányosan szét osztani
def lerp(a, b, t):   return a + (b - a) * t

#korlátozó függvény v nem mehet lo alá v hi fölé
def clamp(v, lo, hi): return max(lo, min(hi, v))

#körön belül pont kiszámitása pl skála vonalak rajzolása, számok helye, mutató vége
def polar(center, radius, angle_deg):
    a = math.radians(angle_deg + 30)
    return (center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius)

#tükrözés függvény pont tükrözése
def mirror_point_x(center, point):
    return (2 * center[0] - point[0], point[1])

#small gauge pontjai tükrözése (fuel)
def gauge_point(center, radius, angle_deg, mirrored=False):
    p = polar(center, radius, angle_deg)
    return mirror_point_x(center, p) if mirrored else p

#szöveg kiiras
def draw_text(surface, txt, font, color, center):
    img = font.render(txt, True, color) 
    surface.blit(img, img.get_rect(center=center))

#ív rajzolás
def draw_arc(surface, color, rect, start_deg, end_deg, width=2):
    pygame.draw.arc(surface, color, rect,
                    math.radians(start_deg), math.radians(end_deg), width)

#réteges glow effektus a körök körül
def draw_glow_circle(surface, color, center, radius, alpha=18, width=0, layers=4):
    glow = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        pygame.draw.circle(glow, (*color, max(3, alpha//i)), center, radius + i*4, width)
    surface.blit(glow, (0, 0))

#szintén csak vonalakra pl mutatók
def draw_glow_line(surface, color, start, end, width=1, alpha=18, layers=3):
    glow = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        pygame.draw.line(glow, (*color, max(2, alpha//i)), start, end, width + i*2)
    surface.blit(glow, (0, 0))

#háttér kirajzolása fényfoltok fekete háttér kékes réteg stb
def draw_background(surface):
    surface.fill(BG)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (20, 35, 60, 30), (180, 30, WIDTH-360, HEIGHT-130))
    pygame.draw.ellipse(glow, (20, 60, 120, 10), (260, 70, WIDTH-520, HEIGHT-220))
    surface.blit(glow, (0, 0))
    pygame.draw.line(surface, (16, 20, 28), (40, 58), (WIDTH-40, 58), 1)

#külső világos gyűrű
def draw_bezel(surface, center, radius):
    pygame.draw.circle(surface, (8, 8, 10),   center, radius+16)
    pygame.draw.circle(surface, (40, 44, 52), center, radius+10, 2)
    pygame.draw.circle(surface, (10, 12, 16), center, radius-8)
    pygame.draw.circle(surface, (24, 28, 36), center, radius-50, 1)
    draw_glow_circle(surface, (100, 140, 210), center, radius-18, alpha=6, width=1, layers=4)

#mutatók
def draw_needle(surface, center, radius, angle_deg, color=RED, needle_width=3, mirrored=False):
    end = gauge_point(center, radius, angle_deg, mirrored)
    shadow_end = gauge_point((center[0]+1, center[1]+1), radius, angle_deg, mirrored)
    pygame.draw.line(surface, (18, 18, 20), center, shadow_end, needle_width+1)
    draw_glow_line(surface, color, center, end, width=1, alpha=18, layers=3)
    pygame.draw.line(surface, color, center, end, needle_width)
    pygame.draw.circle(surface, (10, 10, 12), center, 17)
    pygame.draw.circle(surface, (34, 34, 40), center, 13)
    pygame.draw.circle(surface, color, center, 7)
    pygame.draw.circle(surface, WHITE, center, 2)

#KM/H kijelző
def draw_speedometer(surface, center, radius, speed, font_small, font_tiny, font_big):
    s, e = 140, 400
    draw_bezel(surface, center, radius)
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, s, e, 3)
    draw_arc(surface, RING_DIM, pygame.Rect(rect.x+12, rect.y+12, rect.w-24, rect.h-24), s, e, 1)
    for v in range(0, 331, 10):
        t   = v / 330
        ang = lerp(s, e, t)
        maj = v % 30 == 0
        pygame.draw.line(surface, RING if maj else RING_DIM,
                         polar(center, radius-(30 if maj else 18), ang),
                         polar(center, radius-2, ang), 2 if maj else 1)
        if maj and v > 0:
            lx, ly = polar(center, radius-52, ang)
            draw_text(surface, str(v), font_small, TEXT_FAINT, (lx, ly))
    draw_text(surface, "km/h", font_tiny, WHITE, (center[0], center[1]-90))
    draw_text(surface, str(int(speed)), font_big, WHITE, (center[0], center[1]-45))
    draw_needle(surface, center, radius-28, lerp(s, e, clamp(speed/330, 0, 1)), RED, 3)

# M logo
def draw_m_logo(surface, center):
    x, y = center
    w, h, g = 10, 35, 2
    pygame.draw.rect(surface, M_BLUE1, (x, y, w, h), border_radius=1)
    pygame.draw.rect(surface, M_BLUE2, (x+w+g, y, w, h), border_radius=1)
    pygame.draw.rect(surface, M_RED,   (x+2*(w+g), y, w, h), border_radius=1)

#Fordulat
def draw_tachometer(surface, center, radius, rpm_k, font_small, font_tiny, font_big):
    s, e = 140, 400
    draw_bezel(surface, center, radius)
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, s, e, 3)
    draw_arc(surface, RING_DIM, pygame.Rect(rect.x+12, rect.y+12, rect.w-24, rect.h-24), s, e, 1)
    for i in range(81):
        v   = i / 10.0
        ang = lerp(s, e, v/8)
        maj = i % 10 == 0
        col = RED_BRIGHT if v >= 7.0 else (YELLOW if v >= 6.5 else (RING if maj else RING_DIM))
        pygame.draw.line(surface, col,
                         polar(center, radius-(30 if maj else 18), ang),
                         polar(center, radius-2, ang), 2 if maj else 1)
        if maj and 0 < v < 8:
            lx, ly = polar(center, radius-52, ang)
            draw_text(surface, str(int(v)), font_small, TEXT_FAINT, (lx, ly))
    draw_m_logo(surface, (center[0]-50, center[1]-63))
    draw_text(surface, "M5",    font_big,  WHITE, (center[0]+16, center[1]-45))
    draw_text(surface, "READY", font_tiny, WHITE, (center[0]-78, center[1]+53))
    draw_needle(surface, center, radius-28, lerp(s, e, clamp(rpm_k/8, 0, 1)), RED, 3)

#kicsi kijelzők (hőmérséklet, üzemanyag) tükrözéssel hogy ne kelljen külön rajzolni a skálát
def draw_small_gauge(surface, center, radius, value, min_val, max_val,
                     left_label, center_label, right_label, bottom_label, mirrored, font_tiny):
    s, e = 300, 390
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, *(s-150, e-150) if mirrored else (s, e), 2)
    for i in range(6):
        ang = lerp(s, e, i/5)
        pygame.draw.line(surface, RING_DIM,
                         gauge_point(center, radius-20, ang, mirrored),
                         gauge_point(center, radius-13, ang, mirrored), 1)
    draw_text(surface, str(left_label),   font_tiny, TEXT_DIM, gauge_point(center, radius-32, s, mirrored))
    draw_text(surface, str(right_label),  font_tiny, TEXT_DIM, gauge_point(center, radius-32, e, mirrored))
    draw_text(surface, str(center_label), font_tiny, TEXT_DIM, gauge_point(center, radius-32, (s+e)/2, mirrored))
    draw_text(surface, str(bottom_label), font_tiny, TEXT_DIM, (center[0], center[1]+radius-15))
    t = clamp((value-min_val)/(max_val-min_val), 0, 1)
    draw_needle(surface, center, radius-12, lerp(s, e, t), RED, 2, mirrored=mirrored)

#Limit tábla esztétika
def draw_speed_limit_sign(surface, center, value, font_tiny):
    x, y = center
    pygame.draw.circle(surface, WHITE, (x, y), 20)
    pygame.draw.circle(surface, RED_BRIGHT, (x, y), 20, 3)
    draw_text(surface, str(value), font_tiny, (10, 10, 10), (x, y))

#villogó jelzés ABS, TC, DSC, CHECK
def draw_warning_light(surface, x, y, label, color, font_micro):
    flash = int(time.time() * 3) % 2 == 0
    if flash:
        pygame.draw.rect(surface, color, (x, y, 62, 22), border_radius=4)
        draw_text(surface, label, font_micro, (10, 10, 10), (x+31, y+11))
    else:
        pygame.draw.rect(surface, (30, 30, 35), (x, y, 62, 22), border_radius=4)
        draw_text(surface, label, font_micro, color, (x+31, y+11))

#DTC hiba jelző a jobb felső sarokban, aktív és tárolt DTC-k külön jelzése
def draw_dtc_indicator(surface, font_micro, active_count, stored_count):
    if active_count > 0:
        draw_text(surface, f"DTC: {active_count} aktív",
                  font_micro, RED_BRIGHT, (WIDTH - 100, 20))
    elif stored_count > 0:
        draw_text(surface, f"DTC: {stored_count} tárolt",
                  font_micro, YELLOW, (WIDTH - 100, 20))


def draw_center_panel(surface, fonts, gear=0, vehicle_speed=0.0, coolant_temp=90.0,
                      abs_active=False, tc_active=False, sc_active=False,
                      steering_angle=0.0, torque=0.0, horsepower=0.0,
                      ignition_on=False, engine_running=False, active_dtc_count=0):
    font_huge, font_big, font_mid, font_small, font_tiny, font_micro = fonts
    cx = WIDTH // 2

    if gear == -1:   gear_str, gear_color = "R", YELLOW
    elif gear == 0:  gear_str, gear_color = "N", TEXT_DIM
    else:            gear_str, gear_color = str(gear), WHITE
    draw_text(surface, gear_str, font_huge, gear_color, (cx, 300))

    sf = clamp(steering_angle / 540.0, -1.0, 1.0)
    bw, by = 120, 380
    bx = cx - bw//2
    pygame.draw.rect(surface, (20, 24, 32), (bx, by, bw, 8), border_radius=4)
    mid = bx + bw//2
    fw  = int(abs(sf) * bw // 2)
    if sf >= 0: pygame.draw.rect(surface, BLUE_SOFT, (mid, by, fw, 8), border_radius=2)
    else:       pygame.draw.rect(surface, BLUE_SOFT, (mid-fw, by, fw, 8), border_radius=2)
    pygame.draw.line(surface, TEXT_DIM, (mid, by-2), (mid, by+10), 1)

    draw_text(surface, f"{int(torque)} Nm",     font_tiny, TEXT_DIM, (cx-55, 420))
    draw_text(surface, f"{int(horsepower)} LE", font_tiny, TEXT_DIM, (cx+55, 420))

    warnings = []
    if abs_active:          warnings.append(("ABS",   ORANGE))
    if tc_active:           warnings.append(("TC",    YELLOW))
    if sc_active:           warnings.append(("DSC",   RED_BRIGHT))
    if active_dtc_count > 0: warnings.append(("CHECK", ORANGE))

    wx, wy = cx - 90, 450
    for i, (lbl, col) in enumerate(warnings):
        draw_warning_light(surface, wx + i*68, wy, lbl, col, font_micro)

    pygame.draw.line(surface, BLUE_SOFT, (cx-72, 208), (cx-198, 386), 1)
    pygame.draw.line(surface, BLUE_SOFT, (cx+72, 208), (cx+198, 386), 1)
    draw_speed_limit_sign(surface, (cx-168, 490), 50, font_tiny)

    status, sc = "OFF", TEXT_DIM
    if ignition_on and not engine_running: status, sc = "IGNITION ON",    YELLOW
    elif ignition_on and engine_running:   status, sc = "ENGINE RUNNING",  GREEN
    draw_text(surface, status, font_tiny, sc, (cx, 500))

    y = 540
    pygame.draw.line(surface, (18, 24, 34), (cx-330, y-18), (cx+330, y-18), 1)
    draw_text(surface, time.strftime("%H:%M"),       font_tiny, TEXT, (cx-235, y))
    draw_text(surface, f"{vehicle_speed:.1f} km/h",  font_tiny, TEXT, (cx, y))
    draw_text(surface, f"{coolant_temp:.0f}°C hűtő", font_tiny, TEXT, (cx+235, y))

#gáz és fék trigger tengelyek értékének olvasása, 0.0-1.0 tartományban
def read_trigger_axis(joy, idx):
    if joy is None: return 0.0
    return clamp((joy.get_axis(idx) + 1.0) / 2.0, 0.0, 1.0)

#OBD2 gateway létrehozása és indítása
def make_gateway(dme, dsc, egs, eps):
    gw = OBD2Gateway(port="COM8", dme=dme, dsc=dsc, egs=egs, eps=eps, baudrate=38400)
    gw.start()
    return gw


# =========================
# MAIN
# =========================
def main():
    pygame.init()
    pygame.joystick.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("BMW F90 M5 Cluster")
    clock = pygame.time.Clock()

    font_huge  = pygame.font.SysFont("arial", 78, bold=True)
    font_big   = pygame.font.SysFont("arial", 52, bold=True)
    font_mid   = pygame.font.SysFont("arial", 28, bold=True)
    font_small = pygame.font.SysFont("arial", 19, bold=True)
    font_tiny  = pygame.font.SysFont("arial", 15, bold=False)
    font_micro = pygame.font.SysFont("arial", 12, bold=False)
    fonts = (font_huge, font_big, font_mid, font_small, font_tiny, font_micro)

    dme = DMEModule.DME_Module()
    eps = EPSModule.EPS_Module(dme, None)
    dsc = DSCModule.DSC_Module(None, eps, dme)
    egs = EGSModule.EGS_module(dme, dsc)
    eps.DSC = dsc
    dsc.EGS = egs

    obd2 = make_gateway(dme, dsc, egs, eps)

    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for j in joysticks: j.init()

    ignition_on      = False
    prev_ignition_on = False
    engine_running   = False
    rumble_enabled   = True

    dtc_msg       = ""
    dtc_msg_until = 0.0

    running = True
    while running:
        dt  = clock.tick(FPS) / 1000.0
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYDEVICEADDED:
                joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
                for j in joysticks: j.init()

            elif event.type == pygame.JOYDEVICEREMOVED:
                joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
                for j in joysticks: j.init()

            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == BTN_IGNITION:
                    ignition_on = not ignition_on
                    if not ignition_on:
                        engine_running = False
                        dme.rpm = 0

                elif event.button == BTN_ENGINE and ignition_on:
                    engine_running = not engine_running
                    if not engine_running:
                        dme.rpm = 0

                elif event.button == BTN_DTC_INJECT:
                    # Random DTC injektálás — 2-4 modult érint, modulonként max 2 kód
                    injected = inject_all_modules(dme, dsc, egs, eps, count=2)
                    if injected:
                        dtc_msg = "DTC: " + ", ".join(injected[:6])
                        if len(injected) > 6:
                            dtc_msg += f" (+{len(injected)-6})"
                        dtc_msg_until = now + 5.0

                elif event.button == BTN_DTC_CLEAR:
                    clear_all_modules(dme, dsc, egs, eps)
                    dtc_msg       = "Összes DTC törölve (DME / DSC / EGS / EPS)"
                    dtc_msg_until = now + 3.0

        # Gyújtás átmenet
        if ignition_on and not prev_ignition_on:
            if not obd2.running:
                obd2 = make_gateway(dme, dsc, egs, eps)
        elif not ignition_on and prev_ignition_on:
            obd2.close()
        prev_ignition_on = ignition_on

        joy = joysticks[0] if joysticks else None
        dme.joystick = egs.joystick = dsc.joystick = eps.joystick = joy

        throttle = read_trigger_axis(joy, 5)
        brake    = read_trigger_axis(joy, 4)

        if ignition_on:
            if engine_running:
                target_rpm = IDLE_RPM + throttle * (MAX_RPM - IDLE_RPM)
                dme.rpm += (target_rpm - dme.rpm) * min(1.0, 6.0 * dt)
            else:
                dme.rpm += (0 - dme.rpm) * min(1.0, 8.0 * dt)
                if dme.rpm < 5: dme.rpm = 0

            if joy is not None:
                dme.DME_simulation()
                egs.EGS_Simulation()
                dsc.DSC_simulation()
                eps.EPS_simulation()
            else:
                dme.throttlePosition = 0.0
                dme.DME_simulation()
                egs.EGS_Simulation()
                dsc.brakePosition = brake * 100.0
                dsc.DSC_simulation()
                eps.EPS_simulation()
        else:
            dme.rpm = 0

        if joy is not None and rumble_enabled and engine_running:
            rpm_ratio = clamp((dme.rpm - IDLE_RPM) / (MAX_RPM - IDLE_RPM), 0.0, 0.5)
            try: joy.rumble(rpm_ratio + 0.05, rpm_ratio + 0.05, 80)
            except Exception: pass
        elif joy is not None:
            try: joy.stop_rumble()
            except Exception: pass

        # Értékek
        speed  = clamp(dsc.vehicle_speed, 0.0, 330.0)
        rpm_k  = clamp(dme.rpm / 1000.0, 0.0, 8.0)

        fuel_ratio = dme.fuelLevelLiters / dme.fuelTankLiters
        fuel_value = lerp(0.71, 0.41, fuel_ratio)

        temp = dme.coolantTemp
        tn   = ((temp-70)/30*0.5) if temp <= 100 else (0.5+(temp-100)/70*0.5)
        temp_value = lerp(0.71, 0.41, clamp(tn, 0.0, 1.0))

        active_dtc  = count_active_dtcs(dme, dsc, egs, eps)
        stored_dtc  = count_stored_dtcs(dme, dsc, egs, eps)

        # Rajzolás
        draw_background(screen)
        draw_speedometer(screen, (370, 280),  232, speed, font_small, font_tiny, font_big)
        draw_tachometer( screen, (1030, 280), 232, rpm_k, font_small, font_tiny, font_big)
        draw_small_gauge(screen, (210,  490),  88, fuel_value, 0.41, 0.71, "F",   "1/2", "E",  "km", True,  font_tiny)
        draw_small_gauge(screen, (1190, 490),  88, temp_value, 0.41, 0.71, "170", "100", "70", "°C", False, font_tiny)

        draw_center_panel(screen, fonts,
            gear=egs.GearSelector,
            vehicle_speed=dsc.vehicle_speed,
            coolant_temp=dme.coolantTemp,
            abs_active=dsc.absActive,
            tc_active=dsc.tractionControlActive,
            sc_active=dsc.stabilityControlActive,
            steering_angle=getattr(eps, "steeringAngle", 0.0),
            torque=dme.Torque,
            horsepower=dme.HorsePower,
            ignition_on=ignition_on,
            engine_running=engine_running,
            active_dtc_count=active_dtc,
        )

        draw_dtc_indicator(screen, font_micro, active_dtc, stored_dtc)

        if now < dtc_msg_until and dtc_msg:
            col = ORANGE if "DTC:" in dtc_msg else GREEN
            draw_text(screen, dtc_msg, font_micro, col, (WIDTH//2, HEIGHT-35))

        draw_text(screen,
                  "menu=gyújtás | A=motor | Y=DTC inject | X=DTC törlés",
                  font_micro, TEXT_DIM, (WIDTH//2, HEIGHT-18))

        pygame.display.flip()

    obd2.close()
    pygame.quit()


if __name__ == "__main__":
    main()
