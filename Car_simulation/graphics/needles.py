import pygame
from core.helpers import gauge_point
from graphics.colors import RED, WHITE
from graphics.effects import draw_glow_line

def draw_needle(surface, center, radius, angle_deg, color=RED, needle_width=3, mirrored=False):
    end = gauge_point(center, radius, angle_deg, mirrored)
    shadow_end = gauge_point((center[0] + 1, center[1] + 1), radius, angle_deg, mirrored)
    pygame.draw.line(surface, (18, 18, 20), center, shadow_end, needle_width + 1)
    draw_glow_line(surface, color, center, end, width=1, alpha=18, layers=3)
    pygame.draw.line(surface, color, center, end, needle_width)
    pygame.draw.circle(surface, (10, 10, 12), center, 17)
    pygame.draw.circle(surface, (34, 34, 40), center, 13)
    pygame.draw.circle(surface, color, center, 7)
    pygame.draw.circle(surface, WHITE, center, 2)