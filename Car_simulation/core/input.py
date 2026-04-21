from core.helpers import clamp

def read_trigger_axis(joy, idx):
    if joy is None:
        return 0.0
    return clamp((joy.get_axis(idx) + 1.0) / 2.0, 0.0, 1.0)