import pygame

def draw_glow_circle(surface, color, center, radius, alpha=18, width=0, layers=4):
    glow = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        pygame.draw.circle(glow, (*color, max(3, alpha // i)), center, radius + i * 4, width)
    surface.blit(glow, (0, 0))

def draw_glow_line(surface, color, start, end, width=1, alpha=18, layers=3):
    glow = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        pygame.draw.line(glow, (*color, max(2, alpha // i)), start, end, width + i * 2)
    surface.blit(glow, (0, 0))