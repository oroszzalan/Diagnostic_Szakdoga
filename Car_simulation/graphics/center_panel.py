import time
import pygame

from config import WIDTH
from core.helpers import clamp
from graphics.colors import WHITE, TEXT, TEXT_DIM, YELLOW, GREEN, ORANGE, RED_BRIGHT, BLUE_SOFT
from graphics.text import draw_text
from graphics.indicators import draw_speed_limit_sign, draw_warning_light

def draw_center_panel(surface, fonts, gear=0, vehicle_speed=0.0, coolant_temp=90.0,
                      abs_active=False, tc_active=False, sc_active=False,
                      steering_angle=0.0, torque=0.0, horsepower=0.0,
                      ignition_on=False, engine_running=False, active_dtc_count=0):
    font_huge, font_big, font_mid, font_small, font_tiny, font_micro = fonts
    cx = WIDTH // 2

    if gear == -1:
        gear_str, gear_color = "R", YELLOW
    elif gear == 0:
        gear_str, gear_color = "N", TEXT_DIM
    else:
        gear_str, gear_color = str(gear), WHITE

    draw_text(surface, gear_str, font_huge, gear_color, (cx, 300))

    sf = clamp(steering_angle / 540.0, -1.0, 1.0)
    bw, by = 120, 380
    bx = cx - bw // 2
    pygame.draw.rect(surface, (20, 24, 32), (bx, by, bw, 8), border_radius=4)
    mid = bx + bw // 2
    fw = int(abs(sf) * bw // 2)
    if sf >= 0:
        pygame.draw.rect(surface, BLUE_SOFT, (mid, by, fw, 8), border_radius=2)
    else:
        pygame.draw.rect(surface, BLUE_SOFT, (mid-fw, by, fw, 8), border_radius=2)
    pygame.draw.line(surface, TEXT_DIM, (mid, by-2), (mid, by+10), 1)

    draw_text(surface, f"{int(torque)} Nm", font_tiny, TEXT_DIM, (cx-55, 420))
    draw_text(surface, f"{int(horsepower)} LE", font_tiny, TEXT_DIM, (cx+55, 420))

    warnings = []
    if abs_active:
        warnings.append(("ABS", ORANGE))
    if tc_active:
        warnings.append(("TC", YELLOW))
    if sc_active:
        warnings.append(("DSC", RED_BRIGHT))
    if active_dtc_count > 0:
        warnings.append(("CHECK", ORANGE))

    wx, wy = cx - 90, 450
    for i, (lbl, col) in enumerate(warnings):
        draw_warning_light(surface, wx + i * 68, wy, lbl, col, font_micro)

    pygame.draw.line(surface, BLUE_SOFT, (cx-72, 208), (cx-198, 386), 1)
    pygame.draw.line(surface, BLUE_SOFT, (cx+72, 208), (cx+198, 386), 1)
    draw_speed_limit_sign(surface, (cx-168, 490), 50, font_tiny)

    status, sc = "OFF", TEXT_DIM
    if ignition_on and not engine_running:
        status, sc = "IGNITION ON", YELLOW
    elif ignition_on and engine_running:
        status, sc = "ENGINE RUNNING", GREEN
    draw_text(surface, status, font_tiny, sc, (cx, 500))

    y = 540
    pygame.draw.line(surface, (18, 24, 34), (cx-330, y-18), (cx+330, y-18), 1)
    draw_text(surface, time.strftime("%H:%M"), font_tiny, TEXT, (cx-235, y))
    draw_text(surface, f"{vehicle_speed:.1f} km/h", font_tiny, TEXT, (cx, y))
    draw_text(surface, f"{coolant_temp:.0f}°C hűtő", font_tiny, TEXT, (cx+235, y))