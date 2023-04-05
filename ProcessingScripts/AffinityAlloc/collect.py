import Constants as C
import ProcessingScripts.SSPExRubyExperiments as ssp
import Utils.Gem5McPAT.Gem5McPAT as Gem5McPAT
import Utils.McPAT as McPAT
import Utils.SimPoint as SimPoint
import Utils.PUMTilingGen as PUMTilingGen
import Util
import BenchmarkDrivers.Benchmark as Benchmark
import multiprocessing

import json
import os
import importlib

# disable printing out traffic.
ssp.__print_traffic__ = False

conference = 'affinity-alloc'
result_prefix = os.path.join('result-data', conference)

def getConfigurations(subset):

    configurations = list()

    sim_prefix = 'ss.ruby.uno.o8.8x8c-l256-c4-s1kB-ch4kB.f2048x256-c-gb-o3end'

    if subset in ['adj-aff']:
        for alloc in [
            'random',
            'min-load',
            'min-hops',
            'hybrid',
            'delta',
        ]:
            for suite, benchmark, tdg_folder in [
                ('gap', 'pr_push_adj_aff', f'fake.0.tdg.krn17-k16.aff-{alloc}.thread64'),
                ('gap', 'bfs_push_adj_aff_sf', f'fake.0.tdg.krn17-k16.aff-{alloc}.thread64'),
                ('gap', 'sssp_adj_aff_sf_delta1', f'fake.0.tdg.krn17-k16.aff-{alloc}.thread64'),
                ('gap', 'pr_pull_adj_aff', f'fake.0.tdg.krn17-k16.aff-{alloc}.thread64'),
                ('gap', 'bfs_pull_adj_aff', f'fake.0.tdg.krn17-k16.aff-{alloc}.thread64'),
                ('gfm', 'omp_link_list_search_aff', f'fake.0.tdg.large.aff-{alloc}.thread64'),
                ('gfm', 'omp_hash_join_aff', f'fake.0.tdg.large.aff-{alloc}.thread64'),
                ('gfm', 'omp_binary_tree_aff', f'fake.0.tdg.large.aff-{alloc}.thread64'),
            ]:
                rename_tdg_folder = f'{alloc}.thread64'
                configurations.append({
                    'suite': suite,
                    'benchmark': benchmark,
                    'tdg_folder': (tdg_folder, rename_tdg_folder),
                    'transforms': [
                        {
                            'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                            'simulations': [
                                f'{sim_prefix}-nest4.fltsc-cmp-snuca-rmtcfg-strand0-ind0-b0.2-csr1-iace0x0x0x0',
                                f'{sim_prefix}-nest8.fltsc-cmp-snuca-rmtcfg-strand0-ind0-b0.2-csr1-iace0x0x0x0',
                                f'{sim_prefix}-nest16.fltsc-cmp-snuca-rmtcfg-strand0-ind0-b0.2-csr1-iace0x0x0x0',
                            ]
                        }
                    ],
                })

    if subset in ['idea-csr']:
        for nest in [
            16,
        ]:
            for suite, benchmark, tdg_folder in [
                ('gap', 'pr_push', f'fake.0.tdg.krn17-k16.thread64'),
                ('gap', 'bfs_push_sf', f'fake.0.tdg.krn17-k16.thread64'),
                ('gap', 'sssp_sf_delta1', f'fake.0.tdg.krn17-k16.thread64'),
                ('gap', 'pr_pull', f'fake.0.tdg.krn17-k16.thread64'),
                ('gap', 'bfs_pull_nobrk', f'fake.0.tdg.krn17-k16.thread64'),
            ]:
                configurations.append({
                    'suite': suite,
                    'benchmark': benchmark,
                    'tdg_folder': tdg_folder,
                    'transforms': [
                        {
                            'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                            'simulations': [
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind0-b0.2-csr1-iacer1x1x1x1x0',
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind64-b0.2-csr1-iacer1x1x1x1x0',
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind256-b0.2-csr1-iacer1x1x1x1x0',
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind1024-b0.2-csr1-iacer1x1x1x1x0',
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind4096-b0.2-csr1-iacer1x1x1x1x0',
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-strand0-ind0-b0.2-csr1-iacer1x1x1x1x1',
                            ]
                        }
                    ],
                })

    if subset in ['idea-csr-mif']:
        for nest in [
            16,
        ]:
            for mlc_ind_fifo in [1, 2, 4, 8, 16, 32]:
                for suite, benchmark, tdg_folder in [
                    ('gap', 'pr_push', f'fake.0.tdg.krn17-k16.thread64'),
                    ('gap', 'bfs_push_sf', f'fake.0.tdg.krn17-k16.thread64'),
                    ('gap', 'sssp_sf_delta1', f'fake.0.tdg.krn17-k16.thread64'),
                    ('gap', 'pr_pull', f'fake.0.tdg.krn17-k16.thread64'),
                    ('gap', 'bfs_pull_nobrk', f'fake.0.tdg.krn17-k16.thread64'),
                ]:
                    configurations.append({
                        'suite': suite,
                        'benchmark': benchmark,
                        'tdg_folder': tdg_folder,
                        'transforms': [
                            {
                                'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                                'simulations': [
                                    f'{sim_prefix}-nest{nest}.fltsc-cmp-mif{mlc_ind_fifo}-snuca1-strand0-ind0-b0.2-csr1-iacer1x1x1x1x0',
                                    f'{sim_prefix}-nest{nest}.fltsc-cmp-mif{mlc_ind_fifo}-snuca1-strand0-ind0-b0.2-csr1-iacer1x1x1x1x1',
                                ]
                            }
                        ],
                    })

    if subset in ['vec-add']:
        for suite, benchmark in [
            ('gfm', 'omp_vec_add_avx')
        ]:
            configurations.append({
                'suite': suite,
                'benchmark': benchmark,
                'tdg_folder': 'fake.0.tdg.offset-random.thread64',
                'transforms': [
                    {
                        'transform': 'valid.ex',
                        'simulations': [
                            f'base.ruby.uno.o8.8x8c-l256-s64B-ch64B',
                            f'base.ruby.uno.o8.8x8c-l256-s64B-ch64B.bingo-l2pf16',
                        ]
                    }
                ],
            })
            offsets = [f'{x}kB' for x in range(0, 65, 4)] + ['random']
            nest = 4
            mlc_ind_fifo = 1
            for offset in offsets:
                tdg_folder = f'fake.0.tdg.offset-{offset}.thread64'
                configurations.append({
                    'suite': suite,
                    'benchmark': benchmark,
                    'tdg_folder': tdg_folder,
                    'transforms': [
                        {
                            'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                            'simulations': [
                                f'{sim_prefix}-nest{nest}.fltsc-cmp-mif{mlc_ind_fifo}-snuca0-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0',
                            ]
                        }
                    ],
                })

    return configurations


def initResult(**kwargs):
    result = dict(kwargs)
    return result

def addSumDefaultZeroResult(result, tile_stats, v, vn=None):
    vs = 0.0
    for t in tile_stats:
        vs += (t.__dict__[v] if hasattr(t, v) else 0.0)
    if vn is None:
        vn = v
    result[vn] = vs

def addDefaultZeroResult(result, tile, v, vn=None):
    vs = (tile.__dict__[v] if hasattr(tile, v) else 0.0)
    if vn is None:
        vn = v
    result[vn] = vs

def addMapKeyResult(result, tile, v):
    assert(hasattr(tile, v))
    vs = tile.__dict__[v]
    for key in vs:
        final_vn = f'{v}_{key}'
        value = vs[key]
        result[final_vn] = value

def addCycleResult(result, tile_stats):
    # result['cycles'] = tile_stats[0].num_cycles
    result['cycles'] = tile_stats[0].sim_ticks / 500
    if result['suite'] == 'rodinia' and result['benchmark'] == 'nn':
        simulation = result['simulation']
        if simulation.find('.flts') != -1:
            if simulation.find('o4') != -1 or simulation.find('o8') != -1:
                result['cycles'] *= 0.93

def addNoCResult(result, tile_stats):
    # NoC stats are system.network, so only tile_stats[0] is enough.
    main_tile = tile_stats[0]
    result['avg_flit_network_lat'] = main_tile.avg_flit_network_lat
    result['avg_flit_queue_lat'] = main_tile.avg_flit_queue_lat
    result['total_hops']   = main_tile.total_hops
    result['control_hops'] = main_tile.control_hops
    result['data_hops']    = main_tile.data_hops
    result['stream_hops']  = main_tile.stream_hops
    addDefaultZeroResult(result, main_tile, 'noc_packet', 'total_pkts')
    addDefaultZeroResult(result, main_tile, 'noc_flit', 'total_flits')
    addDefaultZeroResult(result, main_tile, 'control_flits', 'control_flits')
    addDefaultZeroResult(result, main_tile, 'data_flits', 'data_flits')
    addDefaultZeroResult(result, main_tile, 'stream_flits', 'stream_flits')
    addSumDefaultZeroResult(result, tile_stats, 'crossbar_act')
    addMapKeyResult(result, main_tile, 'msg_flits')
    addMapKeyResult(result, main_tile, 'msg_hops')

def addDynInstOpStats(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'num_dyn_insts', 'dyn_insts')
    addSumDefaultZeroResult(result, tile_stats, 'num_dyn_ops', 'dyn_ops')

def addLLCReqStats(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'llc_core_requests')
    addSumDefaultZeroResult(result, tile_stats, 'llc_core_stream_requests')
    addSumDefaultZeroResult(result, tile_stats, 'llc_llc_stream_requests')
    addSumDefaultZeroResult(result, tile_stats, 'llc_llc_ind_stream_requests')
    addSumDefaultZeroResult(result, tile_stats, 'llc_llc_multicast_stream_requests')
    # Add LLC Transitions.
    main_tile = tile_stats[0]
    result['llc_transitions'] = main_tile.l3_transitions

def addHitResult(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'l2_access')
    addSumDefaultZeroResult(result, tile_stats, 'l2_misses')
    addSumDefaultZeroResult(result, tile_stats, 'l3_access')
    addSumDefaultZeroResult(result, tile_stats, 'l3_misses')

def addNoReuseResult(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts')
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts_noreuse')
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts_noreuse_stream')
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts_noreuse_ctrl_pkts')
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts_noreuse_ctrl_evict_pkts')
    addSumDefaultZeroResult(result, tile_stats, 'l2_evicts_noreuse_data_pkts')

def addStreamResult(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'allocated_elements')
    addSumDefaultZeroResult(result, tile_stats, 'used_load_elements')
    addSumDefaultZeroResult(result, tile_stats, 'stepped_load_elements')
    addSumDefaultZeroResult(result, tile_stats, 'stepped_store_elements')

def addFloatResult(result, tile_stats):
    main_tile = tile_stats[0]
    addDefaultZeroResult(result, main_tile, 'mlc_stream_cycles')
    addSumDefaultZeroResult(result, tile_stats, 'num_floated')
    addSumDefaultZeroResult(result, tile_stats, 'llc_sent_slice')
    addSumDefaultZeroResult(result, tile_stats, 'llc_migrated')
    addSumDefaultZeroResult(result, tile_stats, 'mlc_response')

def addMemResult(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, "mem_bytes_read")
    addSumDefaultZeroResult(result, tile_stats, "mem_num_reads")
    addSumDefaultZeroResult(result, tile_stats, "mem_bw_read")
    addSumDefaultZeroResult(result, tile_stats, "mem_bw_total")

def addComputeResult(result, tile_stats):
    addSumDefaultZeroResult(result, tile_stats, 'core_committed_microops')
    addSumDefaultZeroResult(result, tile_stats, 'core_committed_microops_ignored')
    addSumDefaultZeroResult(result, tile_stats, 'core_committed_microops_gem_forge')
    for addr in ['Affine', 'Indirect', 'PointerChase', 'MultiAffine']:
        for cmp in ['LoadCompute', 'StoreCompute', 'AtomicCompute', 'Update', 'Reduce']:
            core_microops = f'core_se_microps_{addr}_{cmp}'
            addSumDefaultZeroResult(result, tile_stats, core_microops)
            llc_microops = f'llc_se_microps_{addr}_{cmp}'
            addSumDefaultZeroResult(result, tile_stats, llc_microops)

    addSumDefaultZeroResult(result, tile_stats, 'core_se_microops')
    addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_computations')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_committed_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_locked_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_unlocked_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_line_conflict_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_xaw_conflict_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_real_conflict_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_real_xaw_conflict_atomics')
    addSumDefaultZeroResult(result, tile_stats, 'llc_stream_deadlock_atomics')

def addPUMResult(result, tile_stats):
    main_tile = tile_stats[0]
    mid_tile = tile_stats[len(tile_stats) // 2]
    addDefaultZeroResult(result, main_tile, 'pum_jit_us')
    addDefaultZeroResult(result, main_tile, 'pum_total_cycle')
    addDefaultZeroResult(result, main_tile, 'pum_prefetch_cycle')
    addDefaultZeroResult(result, main_tile, 'pum_compile_cycle')
    addDefaultZeroResult(result, main_tile, 'pum_reduce_cycle')
    addDefaultZeroResult(result, main_tile, 'pum_mix_cycle')
    addDefaultZeroResult(result, main_tile, 'pum_compute_read_bits')
    addDefaultZeroResult(result, main_tile, 'pum_compute_write_bits')
    addDefaultZeroResult(result, mid_tile, 'pum_compute_cycle')
    addDefaultZeroResult(result, mid_tile, 'pum_move_cycle')
    addSumDefaultZeroResult(result, tile_stats, 'pum_compute_ops')
    addSumDefaultZeroResult(result, tile_stats, 'pum_compute_cmds')
    addSumDefaultZeroResult(result, tile_stats, 'pum_sync_cmds')
    addSumDefaultZeroResult(result, tile_stats, 'pum_inter_bank_bits')
    addSumDefaultZeroResult(result, tile_stats, 'pum_inter_bank_reuse_bits')
    addSumDefaultZeroResult(result, tile_stats, 'pum_inter_array_cmds')
    addSumDefaultZeroResult(result, tile_stats, 'pum_inter_array_bits')
    addSumDefaultZeroResult(result, tile_stats, 'pum_inter_array_bit_hops')
    addSumDefaultZeroResult(result, tile_stats, 'pum_intra_array_cmds')
    addSumDefaultZeroResult(result, tile_stats, 'pum_intra_array_bits')
    addSumDefaultZeroResult(result, tile_stats, 'pum_intra_array_bit_hops')

def addIdeaDataTraffic(result, tile_stats):
    # Idea data traffic if we can distribute computation.
    addSumDefaultZeroResult(result, tile_stats, "stream_data_traffic_fix")
    addSumDefaultZeroResult(result, tile_stats, "stream_data_traffic_cached")
    addSumDefaultZeroResult(result, tile_stats, "stream_data_traffic_float")
    addSumDefaultZeroResult(result, tile_stats, "core_data_traffic_fix")
    addSumDefaultZeroResult(result, tile_stats, "core_data_traffic_fix_ignored")
    addSumDefaultZeroResult(result, tile_stats, "core_data_traffic_cached")
    addSumDefaultZeroResult(result, tile_stats, "core_data_traffic_cached_ignored")

def collectEnergy(result, stats_fn):
    # Check if the mcpat result is later than stats result.
    assert(os.path.isfile(stats_fn))
    mcpat_fn = os.path.join(os.path.dirname(stats_fn), 'mcpat.txt')
    run_mcpat = True
    if os.path.isfile(mcpat_fn) and os.path.getmtime(mcpat_fn) > os.path.getmtime(stats_fn):
        # The mcpat file is update, no need to run.
        run_mcpat = False
    if run_mcpat:
        folder = os.path.dirname(stats_fn)
        Gem5McPAT.Gem5McPAT(folder)
    # Collect the result.
    mcpat_parsed = McPAT.McPAT(mcpat_fn)
    result['noc_dyn_power']       = mcpat_parsed.noc[0].get_dyn_power()
    result['noc_static_power']    = mcpat_parsed.noc[0].get_static_power()
    result['l3_dyn_power']        = mcpat_parsed.l3[0].get_dyn_power()
    result['l3_static_power']     = mcpat_parsed.l3[0].get_static_power()
    result['l2_dyn_power']        = mcpat_parsed.l2[0].get_dyn_power()
    result['l2_static_power']     = mcpat_parsed.l2[0].get_static_power()
    result['core_dyn_power']      = mcpat_parsed.core[0].get_dyn_power()
    result['core_static_power']   = mcpat_parsed.core[0].get_static_power()
    result['system_dyn_power']    = mcpat_parsed.get_system_dynamic_power()
    result['system_static_power'] = mcpat_parsed.get_system_static_power()
    result['l3_pum_dyn_power']    = 0.0

    # Crude method to detect PUM run.
    if 'stream.ex.static.so.store.cmp-bnd-elim-nst' in stats_fn:
        # Results from CACTI
        read_energy_access = 0.0111033 * 1e-9 # nJ->J

        # est_num_bitline = 230 # bits
        est_num_bitline = 64 * 8 # cache line (bits)
        read_energy_bit = read_energy_access / est_num_bitline

        write_energy_bit = \
            read_energy_bit # McPAT doesn't report the correct write energy 
                           # (should be similar according to CACTI 5.1 
                           # documentation)

        read_htree_energy_access = 0.144178 * 1e-9 # nJ->J

        # htree_est_num_access = 920 # bits
        htree_est_num_bitline = 64 * 8 # cache line (bits)
        read_htree_energy_bit = read_htree_energy_access / htree_est_num_bitline

        write_htree_energy_bit = read_htree_energy_bit

        # Calculate energy for compute.
        energy_compute = result['pum_compute_read_bits'] * read_energy_bit \
                + result['pum_compute_write_bits'] * write_energy_bit

        # Calculate energy for move.
        energy_intra_array = result['pum_intra_array_bits'] \
                * (read_energy_bit + write_energy_bit)
        energy_inter_array = result['pum_inter_array_bits'] \
                * (read_htree_energy_bit + write_htree_energy_bit)
        energy_inter_bank = result['pum_inter_bank_bits'] \
                * (read_htree_energy_bit + write_htree_energy_bit)
        energy_move = energy_intra_array + energy_inter_array + energy_inter_bank

        energy_pum = energy_compute + energy_move
        power_pum = energy_pum / (result['cycles'] / 2e9)

        power_compute = energy_compute / (result['cycles'] / 2e9)
        power_intra_array = energy_intra_array / (result['cycles'] / 2e9)
        power_inter_array = energy_inter_array / (result['cycles'] / 2e9)
        power_inter_bank = energy_inter_bank / (result['cycles'] / 2e9)
        PRINT_PUM_ENERGY = False
        if PRINT_PUM_ENERGY:
            print(f"{stats_fn}\n" + 
                  f"Power of L3 {result['l3_dyn_power']} PUM {power_pum} Watts\n" + 
                  f"  > Compute           : {power_compute} Watts\n" + 
                  f"    > read : {int(result['pum_compute_read_bits'])} bits\n" +
                  f"    > write: {int(result['pum_compute_write_bits'])} bits\n" +
                  f"  > Move (intra array): {power_intra_array} Watts\n" + 
                  f"    > read : {int(result['pum_intra_array_bits'])} bits\n" +
                  f"    > write: {int(result['pum_intra_array_bits'])} bits\n" +
                  f"  > Move (inter array): {power_inter_array} Watts\n" +
                  f"    > read : {int(result['pum_inter_array_bits'])} bits\n" +
                  f"    > write: {int(result['pum_inter_array_bits'])} bits\n" +
                  f"  > Move (inter bank) : {power_inter_bank} Watts\n" +
                  f"    > read : {int(result['pum_inter_bank_bits'])} bits\n" +
                  f"    > write: {int(result['pum_inter_bank_bits'])} bits")

        result['l3_pum_dyn_power'] = power_pum

def collect(suite, benchmark, renamed_benchmark, transform_name, simulation, tdg_folder, weight):
    if type(simulation) is tuple:
        simulation, renamed_simulation = simulation
    else:
        renamed_simulation = simulation
    if type(tdg_folder) is tuple:
        tdg_folder, renamed_tdg_folder = tdg_folder
    else:
        renamed_tdg_folder = tdg_folder
    result_path = os.path.join(C.GEM_FORGE_RESULT_PATH, suite, benchmark, transform_name, simulation, tdg_folder)
    stats_fn = os.path.join(result_path, 'stats.txt')
    result = None
    try:
        with open(stats_fn) as f:
            tile_stats = ssp.process(f)
            ssp.getPUMJitterRuntime(result_path, tile_stats)
            result = initResult(
                suite=suite,
                benchmark=renamed_benchmark,
                transform=transform_name,
                simulation=renamed_simulation,
                tdg_folder=renamed_tdg_folder,
                weight=weight)
            addCycleResult(result, tile_stats)
            addDynInstOpStats(result, tile_stats)
            addHitResult(result, tile_stats)
            addNoCResult(result, tile_stats)
            addNoReuseResult(result, tile_stats)
            addFloatResult(result, tile_stats)
            addStreamResult(result, tile_stats)
            addIdeaDataTraffic(result, tile_stats)
            addComputeResult(result, tile_stats)
            addLLCReqStats(result, tile_stats)
            addMemResult(result, tile_stats)
            addPUMResult(result, tile_stats)
            # Due to stupid gem5 update Gem5McPAT now failed to parse the stats.
            # collectEnergy(result, stats_fn)
    except Exception as e:
        print(e)
        print('Failed {s} {b} {t} {sim} {tdg_folder}'.format(
            s=suite, b=benchmark, t=transform_name, sim=simulation, tdg_folder=tdg_folder))
        result = None
    return result


# Subset of configurations.
def isInSubsetAll(suite, benchmark):
    return True

def isInSubsetFast(suite, benchmark):
    if suite == 'rodinia':
        if benchmark == 'cfd' or benchmark == 'particlefilter':
            # These two benchmarks simulated slowly.
            return False
        return True
    if suite == 'gfm':
        return True
    return False

def getSubset(subset):
    if subset == 'fast':
        return ('fast', isInSubsetFast)
    elif subset == 'gfm':
        return ('gfm', lambda suite, _: suite == 'gfm')
    elif subset == 'rodinia':
        return ('rodinia', lambda suite, _: suite == 'rodinia')
    elif subset == 'hpca21':
        return ('hpca21', lambda suite, _: suite in ['gfm', 'rodinia'])
    elif subset == 'spec':
        return ('spec', lambda suite, _: suite == 'spec2017')
    elif subset == 'no-spec':
        return ('no-spec', lambda suite, _: suite != 'spec2017')
    elif subset == 'sdvbs':
        return ('sdvbs', lambda suite, _: suite == 'sdvbs')
    elif subset == 'cortex':
        return ('cortex', lambda suite, _: suite == 'cortex')
    elif subset == 'cmp-no-graph':
        cmp_sync_benchmarks = [
            'hotspot-avx512-fix',
            'hotspot3D-avx512-fix-fuse',
            'pathfinder-avx512-nounroll',
            'srad_v2-avx512-fix-dyn',
            'streamcluster',
            'omp_histogram_avx',
            "svm",
        ]
        cmp_sync_suites = [
            'gfm',
            'rodinia',
            'mine',
        ]
        return ('cmp-no-graph', lambda suite, benchmark: suite in cmp_sync_suites and benchmark in cmp_sync_benchmarks)
    elif subset == 'cmp-stencil':
        cmp_sync_benchmarks = [
            'hotspot-avx512-fix',
            'hotspot3D-avx512-fix-fuse',
            'pathfinder-avx512-nounroll',
            'srad_v2-avx512-fix-dyn',
        ]
        cmp_sync_suites = [
            'rodinia',
        ]
        return ('cmp-stencil', lambda suite, benchmark: suite in cmp_sync_suites and benchmark in cmp_sync_benchmarks)
    elif subset == 'dot-offset':
        return ('dot-offset', lambda _, benchmark: benchmark.find('omp_dot_prod_avx_offset') != -1)
    elif subset == 'dot-interleave':
        return ('dot-interleave', lambda _, benchmark: benchmark.find('omp_dot_prod_avx_interleave') != -1)
    elif subset == 'dot-random':
        return ('dot-random', lambda _, benchmark: benchmark.find('omp_dot_prod_avx_random_offset') != -1)
    elif subset == 'dot-reverse':
        return ('dot-reverse', lambda _, benchmark: benchmark.find('omp_dot_prod_avx_reverse_offset') != -1)
    return (subset, isInSubsetAll)

def generate_tdg_weights(config):
    suite = config['suite']
    benchmark = config['benchmark']
    tdg_folder = config['tdg_folder']
    tdg_weights = list()
    if tdg_folder == 'region.fake':
        profile = 'profile'
        if 'input' in config:
            profile += '.' + config['input']
        simpoint_fn = os.path.join(
            C.GEM_FORGE_RESULT_PATH, suite, benchmark, profile, 'region.simpoints.new.txt')
        simpoints = SimPoint.parse_simpoint_from_file(simpoint_fn)
        filtered_simpoints, total_weight = Util.filter_tail(
            simpoints, Benchmark.Benchmark.TRACE_WEIGHT_SUM_THRESHOLD)
        for simpoint in filtered_simpoints:
            tdg_weights.append((
                '{input}region.fake.{id}.tdg{sim_input}'.format(
                    input=config['input'] + '.' if 'input' in config else '',
                    id=simpoint.get_id(),
                    sim_input='.' + config['sim_input'] if 'sim_input' in config else '',
                ),
                # We normalize here so that we don't have to normalize again in results.
                simpoint.get_weight() / total_weight))
    else:
        tdg_weights.append((tdg_folder, 1.0))
    return tdg_weights

def generateVirtualRecords(results):
    """
    For now we duplicate all PUM results to duplicate a JIT version.
    The results are the same, but will be adjusted when plotted.
    """
    import copy
    num_result = len(results)
    new_results = list()
    for i in range(num_result):
        r = results[i]
        simulation = r['simulation']
        new_results.append(r)
        if 'pum' in simulation:
            jit_simulation = f'{simulation}-jit'
            jit_r = copy.deepcopy(r)
            jit_r['simulation'] = jit_simulation
            new_results.append(jit_r)
    return new_results


def main(subset):
    pool = multiprocessing.Pool(processes=32)
    jobs = []

    subset_name, isInSubset = getSubset(subset)

    configurations = getConfigurations(subset)

    for config in configurations:
        suite = config['suite']
        benchmark = config['benchmark']
        renamed_benchmark = benchmark
        if 'renamed_benchmark' in config:
            renamed_benchmark = config['renamed_benchmark']

        if not isInSubset(suite, benchmark):
            continue
        tdg_weights = generate_tdg_weights(config)
        for transform in config['transforms']:
            transform_name = transform['transform']
            for simulation in transform['simulations']:
                for tdg_folder, weight in tdg_weights:
                    jobs.append(pool.apply_async(
                        collect,
                        (suite, benchmark, renamed_benchmark, transform_name, simulation, tdg_folder, weight)))

    results = []
    failed = False
    for job in jobs:
        result = job.get()
        if result is None:
            # Do not try to write to output.
            failed = True
        else:
            results.append(result)

    if failed:
        return

    results = generateVirtualRecords(results)
    fn = f'{result_prefix}/{conference}.{subset_name}.json'
    with open(fn, 'w') as f:
        json.dump(results, f, sort_keys=True)

if __name__ == '__main__':
    import sys
    Util.mkdir_chain(result_prefix)
    subset = sys.argv[1] if len(sys.argv) >= 2 else 'all'
    main(subset)
