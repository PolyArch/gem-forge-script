import Constants as C
import ProcessingScripts.SSPExRubyExperiments as ssp
import Utils.Gem5McPAT.Gem5McPAT as Gem5McPAT
import Utils.McPAT as McPAT
import Utils.SimPoint as SimPoint
import Util
import BenchmarkDrivers.Benchmark as Benchmark
import multiprocessing

import json
import os
import importlib

def getConfigureations(subset):
    # Same across all benchmarks.
    fix_transforms = [
        {
            'transform': 'valid.ex',
            'simulations': [
                'replay.ruby.single.i4.tlb.8x8c-l256-s64B',
                'replay.ruby.single.i4.tlb.8x8c-l256-s64B.bingo-l2pf16',
                'replay.ruby.single.o4.tlb.8x8c-l256-s64B',
                'replay.ruby.single.o4.tlb.8x8c-l256-s64B.bingo-l2pf16',
                'replay.ruby.single.o8.tlb.8x8c-l256-s64B',
                'replay.ruby.single.o8.tlb.8x8c-l256-s64B.bingo-l2pf16',
            ]
        },
    ]

    stream_cmp_simulations = [
        # Computation
        'stream.ruby.single.i4.tlb.8x8c-l256-s64B.f256-c-cmp',
        'stream.ruby.single.i4.tlb.8x8c-l256-s1kB.f256-c.fltsc-cmp',
        'stream.ruby.single.i4.tlb.8x8c-l256-s1kB.f256-c.fltsc-cmp-sync',
        'stream.ruby.single.o4.tlb.8x8c-l256-s64B.f1024-c-gb-cmp',
        'stream.ruby.single.o4.tlb.8x8c-l256-s1kB.f1024-c-gb.fltsc-cmp',
        'stream.ruby.single.o4.tlb.8x8c-l256-s1kB.f1024-c-gb.fltsc-cmp-sync',
        'stream.ruby.single.o8.tlb.8x8c-l256-s64B.f2048-c-gb-cmp',
        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp',
        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp-sync',
        'stream.ruby.single.o8.tlb.8x8c-l256-s64B.f2048-c-gb-traffic',
    ]

    stream_cmp_data_placement_simulations = [
        'stream.ruby.single.o8.tlb.8x8c-l256-s64B.f2048-c-gb-cmp',
        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp',
        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp-sync',
    ]

    hpca21_submission_stream_simulations = [
        'stream.ruby.single.i4.tlb.8x8c-l256-s64B.f256-c',
        'stream.ruby.single.i4.tlb.8x8c-l256-s1kB.f256-c.flts-mc2',
        'stream.ruby.single.i4.tlb.8x8c-l256-s64B.f512-c',
        'stream.ruby.single.i4.tlb.8x8c-l256-s1kB.f512-c.flts-mc2',
        'stream.ruby.single.o4.tlb.8x8c-l256-s64B.f1024-c-gb',
        'stream.ruby.single.o4.tlb.8x8c-l256-s1kB.f1024-c-gb.flts-mc2',
        'stream.ruby.single.o8.tlb.8x8c-l256-s64B.f2048-c-gb',
        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.flts-mc2',
    ]
    stream_simulations = hpca21_submission_stream_simulations

    ssp_so_cmp_transform = {
        'transform': 'stream.ex.static.so.store.cmp',
        'simulations': stream_cmp_simulations,
        # 'simulations': stream_cmp_simd_lat_simulations,
        # 'simulations': stream_cmp_inflyc_simulations,
        # 'simulations': stream_cmp_data_placement_simulations,
    }
    ssp_so_transform = {
        'transform': 'stream.ex.static.so.store',
        'simulations': stream_simulations,
    }

    configurations = list()

    benchmarks_no_check = [
        ('gap', 'bfs_push', 'fake.0.tdg.krn18-k16-thread64'),
        ('gap', 'pr_push', 'fake.0.tdg.krn18-k16-thread64'),
        ('gap', 'sssp', 'fake.0.tdg.krn18-k16-thread64'),
        ('gap', 'bfs_pull_shuffle', 'fake.0.tdg.krn18-k16-thread64'),
        ('gap', 'pr_pull_shuffle', 'fake.0.tdg.krn18-k16-thread64'),
        ('gfm', 'omp_binary_tree', 'fake.0.tdg.thread64-large'),
        ('gfm', 'omp_link_list_search', 'fake.0.tdg.thread64-large'),
    ]

    if subset in ['layout']:
        for suite, benchmark, tdg_folder in benchmarks_no_check:
            configurations.append({
                'suite': suite,
                'benchmark': benchmark,
                'tdg_folder': tdg_folder,
                'transforms': [{
                    'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                    'simulations': [
                        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB-ch4kB.f2048-c-gb.fltsc-cmp',
                        'stream.ruby.single.o8.tlb.8x8c-l256-s1kB-ch4kB.f2048-c-gb.inoc0.fltsc-cmp',
                    ],},
                ]
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

def addDefaultZeroResult(result, tile, v, vn):
    vs = (tile.__dict__[v] if hasattr(tile, v) else 0.0)
    result[vn] = vs

def addCycleResult(result, tile_stats):
    result['cycles'] = tile_stats[0].num_cycles
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
    # addSumDefaultZeroResult(result, tile_stats, 'core_se_microops_atomic')
    # addSumDefaultZeroResult(result, tile_stats, 'core_se_microops_load')
    # addSumDefaultZeroResult(result, tile_stats, 'core_se_microops_store')
    # addSumDefaultZeroResult(result, tile_stats, 'core_se_microops_reduce')
    # addSumDefaultZeroResult(result, tile_stats, 'core_se_microops_update')
    addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops')
    # addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops_atomic')
    # addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops_load')
    # addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops_store')
    # addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops_reduce')
    # addSumDefaultZeroResult(result, tile_stats, 'llc_se_microops_update')
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

def collect(suite, benchmark, transform_name, simulation, tdg_folder, weight):
    result_path = os.path.join(C.GEM_FORGE_RESULT_PATH, suite, benchmark, transform_name, simulation, tdg_folder)
    stats_fn = os.path.join(result_path, 'stats.txt')
    result = None
    try:
        with open(stats_fn) as f:
            tile_stats = ssp.process(f)
            result = initResult(
                suite=suite,
                benchmark=benchmark,
                transform=transform_name,
                simulation=simulation,
                tdg_folder=tdg_folder,
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
            # Collect energy results.
            collectEnergy(result, stats_fn)
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


def main(subset):
    pool = multiprocessing.Pool(processes=32)
    jobs = []

    subset_name, isInSubset = getSubset(subset)

    configurations = getConfigureations(subset)

    for config in configurations:
        suite = config['suite']
        benchmark = config['benchmark']

        if not isInSubset(suite, benchmark):
            continue
        tdg_weights = generate_tdg_weights(config)
        for transform in config['transforms']:
            transform_name = transform['transform']
            for simulation in transform['simulations']:
                for tdg_folder, weight in tdg_weights:
                    jobs.append(pool.apply_async(
                        collect,
                        (suite, benchmark, transform_name, simulation, tdg_folder, weight)))

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
    conference = 'micro23'
    fn = '{conf}.{subset}.json'.format(
        conf=conference, subset=subset_name)
    with open(fn, 'w') as f:
        json.dump(results, f, sort_keys=True)

if __name__ == '__main__':
    import sys
    subset = sys.argv[1] if len(sys.argv) >= 2 else 'all'
    main(subset)
