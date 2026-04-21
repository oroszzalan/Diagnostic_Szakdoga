import math

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def polar(center, radius, angle_deg):
    a = math.radians(angle_deg + 30)
    return (center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius)

def mirror_point_x(center, point):
    return (2 * center[0] - point[0], point[1])

def gauge_point(center, radius, angle_deg, mirrored=False):
    p = polar(center, radius, angle_deg)
    return mirror_point_x(center, p) if mirrored else p