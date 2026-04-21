import random

def inject_all_modules(sim, count=2):
    dme, dsc, egs, eps = sim.modules()
    all_injected = []
    modules = [dme, dsc, egs, eps]
    affected = random.sample(modules, k=random.randint(2, len(modules)))
    for mod in affected:
        injected = mod.inject_random_faults(count=count)
        all_injected.extend(injected)
    return all_injected

def clear_all_modules(sim):
    for mod in sim.modules():
        mod.clear_all_faults()

def count_active_dtcs(sim):
    return sum(len(mod.activeDTC) for mod in sim.modules())

def count_stored_dtcs(sim):
    return sum(len(mod.storedDTC) for mod in sim.modules())