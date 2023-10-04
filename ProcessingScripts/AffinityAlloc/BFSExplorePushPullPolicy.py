import os
import json
from pprint import pprint

import Constants as C

def get_work_item_fn(workload, transform, simulation, graph):
    result_folder = '/benchmarks/llvm-tdg-results/stream/gap'
    return f'{result_folder}/{workload}/{transform}/{simulation}/{graph}/ftrace/work_item.system'

def read_work_item_cycles(workload, transform, simulation, graph):
    fn = get_work_item_fn(workload, transform, simulation, graph)
    cycles = list()
    with open(fn) as f:
        for line in f:
            fields = line.split()
            cycles.append(int(fields[3]))
    return cycles

def generate_oracle_switch(workload_push, workload_pull, transform, simulation, tdg_folder):
    push_cycles = read_work_item_cycles(workload_push, transform, simulation, tdg_folder)
    pull_cycles = read_work_item_cycles(workload_pull, transform, simulation, tdg_folder)
    if len(push_cycles) != len(pull_cycles):
        print("Mismatch between push and pull iterations?!")
    iters = len(push_cycles)
    diff = [push_cycles[i] - pull_cycles[i] for i in range(iters)]
    print(diff)
    total_push_cycles = sum(push_cycles)
    total_pull_cycles = sum(pull_cycles)
    total_min_cycles = sum(min(push_cycles[i], pull_cycles[i]) for i in range(iters))
    print(f'  Push {total_push_cycles} Pull {total_pull_cycles} Min {total_min_cycles} {total_push_cycles / total_min_cycles:.4f}')
    
    # Compute switch point.
    is_push = True
    switch_points = list()
    for i in range(iters):
        if is_push:
            if diff[i] > 0:
                # Switch to pull.
                is_push = False
                switch_points.append((i, False))
        else:
            if diff[i] < 0:
                # Switch to push.
                is_push = True
                switch_points.append((i, True))

    print(f'  Switch {switch_points}')
    return switch_points


def main():
    graphs = [
        'krn15-k64',
        'krn16-k32',
        'krn17-k16',
        'krn18-k8',
        'krn19-k4',
        'krn20-k2',
    ]
    affinity_policies = [
        'hybrid5',
        'min-hops',
        'random',
    ]
    oracle_switch_points = list()

    stream_transform = 'stream.ex.static.so.store.cmp-bnd-elim-nst'
    aff_alloc_sim = 'ss.ruby.uno.o8.8x8c-l256-c4-s1kB-ch4kB.f2048x256-c-gb-o3end-nest16.fltsc-cmp-mif8-snuca1-rmt-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
    aff_alloc_workload_push = 'bfs_push_adj_uno_aff_sf'
    aff_alloc_workload_pull = 'bfs_pull_adj_uno_aff'
    aff_alloc_workload_both = 'bfs_both_adj_uno_aff_sf'

    nsc_sim = 'ss.ruby.uno.o8.8x8c-l256-c4-s1kB-ch4kB.f2048x256-c-gb-o3end-nest16.fltsc-cmp-mif8-snuca1x1-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
    nsc_workload_push = 'bfs_push_sf'
    nsc_workload_pull = 'bfs_pull'
    nsc_workload_both = 'bfs_both_sf'

    for graph in graphs:
        # Affinity Alloc.
        for policy in affinity_policies:
            transform = stream_transform
            simulation = aff_alloc_sim
            print(f'-- Affinity Alloc {graph} {policy}')
            tdg_folder = f'fake.0.tdg.{graph}-rnd64.aff-{policy}.thread64'
            switch_points = generate_oracle_switch(aff_alloc_workload_push, aff_alloc_workload_pull, transform, simulation, tdg_folder)
            oracle_switch_points.append((aff_alloc_workload_both, transform, simulation, tdg_folder, switch_points))

    for graph in graphs + ['ego-gplus', 'twitch-gamers']:
        # NSC. 
        transform = stream_transform
        simulation = nsc_sim
        print(f'-- NSC {graph}')
        tdg_folder = f'fake.0.tdg.{graph}-rnd64.thread64'
        switch_points = generate_oracle_switch(nsc_workload_push, nsc_workload_pull, transform, simulation, tdg_folder)
        oracle_switch_points.append((nsc_workload_both, transform, simulation, tdg_folder, switch_points))
        

    print('-- Oracle switch points')
    pprint(oracle_switch_points)

    switch_fn = f'{C.GEM_FORGE_DRIVER_PATH}/BenchmarkDrivers/gap_bfs_push_pull_switch.json'
    with open(switch_fn, 'w') as f:
        json.dump(oracle_switch_points, f)
            

if __name__ == '__main__':
    main()