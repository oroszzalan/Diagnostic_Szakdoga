def draw_text(surface, txt, font, color, center):
    img = font.render(txt, True, color)
    surface.blit(img, img.get_rect(center=center))