def destuff_can_bits(stuffed: str) -> str:
    if not stuffed:
        return ""
    out = [stuffed[0]]
    run = 1
    i = 1
    while i < len(stuffed):
        b = stuffed[i]
        run = run + 1 if b == out[-1] else 1
        out.append(b)
        i += 1
        if run == 5:
            if i < len(stuffed):
                i += 1
            run = 1
    return "".join(out)


def reconstruct_frame_from_stuffed(stuffed_bits: str) -> str:
    if len(stuffed_bits) < 10:
        raise ValueError("Frame too short")
    return destuff_can_bits(stuffed_bits[:-9]) + stuffed_bits[-9:]
