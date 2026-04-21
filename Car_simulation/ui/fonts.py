import pygame

def create_fonts():
    font_huge  = pygame.font.SysFont("arial", 78, bold=True)
    font_big   = pygame.font.SysFont("arial", 52, bold=True)
    font_mid   = pygame.font.SysFont("arial", 28, bold=True)
    font_small = pygame.font.SysFont("arial", 19, bold=True)
    font_tiny  = pygame.font.SysFont("arial", 15, bold=False)
    font_micro = pygame.font.SysFont("arial", 12, bold=False)
    return (font_huge, font_big, font_mid, font_small, font_tiny, font_micro)