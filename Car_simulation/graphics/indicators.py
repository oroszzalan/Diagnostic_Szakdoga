import time
import pygame

from config import WIDTH
from graphics.colors import WHITE, RED_BRIGHT, YELLOW
from graphics.text import draw_text

def draw_speed_limit_sign(surface, center, value, font_tiny):
    x, y = center
    pygame.draw.circle(surface, WHITE, (x, y), 20)
    pygame.draw.circle(surface, RED_BRIGHT, (x, y), 20, 3)
    draw_text(surface, str(value), font_tiny, (10, 10, 10), (x, y))

def draw_warning_light(surface, x, y, label, color, font_micro):
    flash = int(time.time() * 3) % 2 == 0
    if flash:
        pygame.draw.rect(surface, color, (x, y, 62, 22), border_radius=4)
        draw_text(surface, label, font_micro, (10, 10, 10), (x+31, y+11))
    else:
        pygame.draw.rect(surface, (30, 30, 35), (x, y, 62, 22), border_radius=4)
        draw_text(surface, label, font_micro, color, (x+31, y+11))

def draw_dtc_indicator(surface, font_micro, active_count, stored_count):
    if active_count > 0:
        draw_text(surface, f"DTC: {active_count} aktív", font_micro, RED_BRIGHT, (WIDTH - 100, 20))
    elif stored_count > 0:
        draw_text(surface, f"DTC: {stored_count} tárolt", font_micro, YELLOW, (WIDTH - 100, 20))