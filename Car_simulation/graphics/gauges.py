import math
import pygame

from core.helpers import lerp, clamp, polar
from graphics.colors import (
    WHITE, TEXT_FAINT, RING, RING_DIM, RED, RED_BRIGHT, YELLOW,
    TEXT_DIM, M_BLUE1, M_BLUE2, M_RED
)
from graphics.text import draw_text
from graphics.needles import draw_needle
from graphics.background import draw_bezel

def draw_arc(surface, color, rect, start_deg, end_deg, width=2):
    pygame.draw.arc(surface, color, rect, math.radians(start_deg), math.radians(end_deg), width)

def draw_m_logo(surface, center):
    x, y = center
    w, h, g = 10, 35, 2
    pygame.draw.rect(surface, M_BLUE1, (x, y, w, h), border_radius=1)
    pygame.draw.rect(surface, M_BLUE2, (x+w+g, y, w, h), border_radius=1)
    pygame.draw.rect(surface, M_RED,   (x+2*(w+g), y, w, h), border_radius=1)

def draw_speedometer(surface, center, radius, speed, font_small, font_tiny, font_big):
    s, e = 140, 400
    draw_bezel(surface, center, radius)
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, s, e, 3)
    draw_arc(surface, RING_DIM, pygame.Rect(rect.x+12, rect.y+12, rect.w-24, rect.h-24), s, e, 1)

    for v in range(0, 331, 10):
        t = v / 330
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

def draw_tachometer(surface, center, radius, rpm_k, font_small, font_tiny, font_big):
    s, e = 140, 400
    draw_bezel(surface, center, radius)
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, s, e, 3)
    draw_arc(surface, RING_DIM, pygame.Rect(rect.x+12, rect.y+12, rect.w-24, rect.h-24), s, e, 1)

    for i in range(81):
        v = i / 10.0
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
    draw_text(surface, "M5", font_big, WHITE, (center[0]+16, center[1]-45))
    draw_text(surface, "READY", font_tiny, WHITE, (center[0]-78, center[1]+53))
    draw_needle(surface, center, radius-28, lerp(s, e, clamp(rpm_k/8, 0, 1)), RED, 3)

def draw_small_gauge(surface, center, radius, value, min_val, max_val,
                     left_label, center_label, right_label, bottom_label, mirrored, font_tiny):
    from core.helpers import gauge_point
    s, e = 300, 390
    rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    draw_arc(surface, RING, rect, *(s-150, e-150) if mirrored else (s, e), 2)

    for i in range(6):
        ang = lerp(s, e, i/5)
        pygame.draw.line(surface, RING_DIM,
                         gauge_point(center, radius-20, ang, mirrored),
                         gauge_point(center, radius-13, ang, mirrored), 1)

    draw_text(surface, str(left_label), font_tiny, TEXT_DIM, gauge_point(center, radius-32, s, mirrored))
    draw_text(surface, str(right_label), font_tiny, TEXT_DIM, gauge_point(center, radius-32, e, mirrored))
    draw_text(surface, str(center_label), font_tiny, TEXT_DIM, gauge_point(center, radius-32, (s+e)/2, mirrored))
    draw_text(surface, str(bottom_label), font_tiny, TEXT_DIM, (center[0], center[1]+radius-15))

    t = clamp((value-min_val)/(max_val-min_val), 0, 1)
    draw_needle(surface, center, radius-12, lerp(s, e, t), RED, 2, mirrored=mirrored)