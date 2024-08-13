import math


def satisfy_deferables(tick, deferables, max_alloc_total):

    tick_to_energy = {}

    for deferable in deferables:
        if deferable.end not in tick_to_energy:
            tick_to_energy[deferable.end] = 0
        tick_to_energy[deferable.end] += deferable.energy

    tick_to_energy = dict(sorted(tick_to_energy.items(), key=lambda x: -x[0]))

    end_to_allocations = {}  # {59: [59, 58, 57, 56]}

    for end, energy in tick_to_energy.items():
        if energy == 0:
            continue
        new_end = end
        for end2, ticks_allocated in end_to_allocations.items():
            if ticks_allocated[0] <= end:
                new_end = ticks_allocated[0] - 1
                continue

        ticks_required = math.ceil(energy / max_alloc_total)

        ticks_allocating = [new_end - i for i in range(ticks_required)]
        ticks_allocating.reverse()

        end_to_allocations[end] = ticks_allocating

    allocations = [0] * len(deferables)
    for end, ticks_allocated in end_to_allocations.items():
        for t in ticks_allocated:
            if t != tick.tick:
                continue
            for i, d in enumerate(deferables):
                if d.end == end:
                    allocation = max_alloc_total * (d.energy / tick_to_energy[end])
                    allocation = min(allocation, d.energy)
                    d.energy -= allocation

                    allocations[i] = allocation

    # for i in allocations:
    #     if i != 0:
    #         print(f"Tick: {tick.tick}, Allocations: {allocations}")
    #         break

    return allocations


def satisfy_deferables_start(tick, deferables, total_energy, max_import_energy):
    allocations = [0] * len(deferables)
    energy_left = max_import_energy + total_energy
    for i, d in enumerate(deferables):
        if d.start <= tick.tick and d.energy != 0:
            allocation = min(energy_left, d.energy)
            d.energy -= allocation
            energy_left -= allocation
            allocations[i] = allocation
    return allocations
