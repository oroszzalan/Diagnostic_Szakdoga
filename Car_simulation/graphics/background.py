import pygame
from config import WIDTH, HEIGHT
from graphics.colors import BG
from graphics.effects import draw_glow_circle

def draw_background(surface):
    surface.fill(BG)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (20, 35, 60, 30), (180, 30, WIDTH-360, HEIGHT-130))
    pygame.draw.ellipse(glow, (20, 60, 120, 10), (260, 70, WIDTH-520, HEIGHT-220))
    surface.blit(glow, (0, 0))
    pygame.draw.line(surface, (16, 20, 28), (40, 58), (WIDTH-40, 58), 1)

def draw_bezel(surface, center, radius):
    pygame.draw.circle(surface, (8, 8, 10), center, radius + 16)
    pygame.draw.circle(surface, (40, 44, 52), center, radius + 10, 2)
    pygame.draw.circle(surface, (10, 12, 16), center, radius - 8)
    pygame.draw.circle(surface, (24, 28, 36), center, radius - 50, 1)
    draw_glow_circle(surface, (100, 140, 210), center, radius - 18, alpha=6, width=1, layers=4)