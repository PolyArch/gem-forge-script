import Constants as C
import Util
import Utils.StreamFloatTraceReader as StreamFloatTraceReader
import BenchmarkDrivers.Benchmark as Benchmark
import multiprocessing

import json
import os
import importlib

conference = 'affinity-alloc'
result_prefix = os.path.join('result-data', conference)

StreamFloatTraceReader.enable_print = True 

def getConfigurations(subset):

    configurations = list()

    sim_prefix = 'ss.ruby.uno.o8.8x8c-l256-c4-s1kB-ch4kB.f2048x256-c-gb-o3end'


    if subset in ['float-trace']:
        for nest in [
            # 4,
            # 8,
            16,
        ]:
            sim = f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-rmt-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
            for suite, benchmark, abbrev, sim_input, keyword in [
                ('gap', 'pr_push_adj_uno_aff', 'pr_push_adj', 'krn17-k16-rnd64', 'score.at'),
                ('gap', 'bfs_push_adj_uno_aff_sf', 'bfs_push_adj', 'krn17-k16-rnd64', 'swap.at'),
                # ('gfm', 'omp_link_list_search_aff', 'link-list', 'large', 'link_list.next.ld'),
                # ('gfm', 'omp_hash_join_aff', 'hash-join', 'large', 'hash_join.next.ld'),
            ]:
                for alloc_policy in [
                    'hybrid5',
                    'min-hops',
                    'min-load',
                    'random',
                    # 'delta',
                ]:
                    tdg_folder = f'fake.0.tdg.{sim_input}.aff-{alloc_policy}.thread64'
                    out_fn = f'{result_prefix}/{conference}.{abbrev}.{alloc_policy}.nest{nest}'
                    configurations.append({
                        'suite': suite,
                        'benchmark': benchmark,
                        'tdg_folder': tdg_folder,
                        'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                        'keyword': keyword,
                        'simulation': sim,
                        'out_fn': out_fn,
                    })

    if subset in ['gfm']:
        for nest in [
            16,
        ]:
            for suite, benchmark, abbrev, sim_input, keyword in [
                ('gfm', 'omp_stencil3d_avx', 'stencil3d', 'medium', '43(store)'),
            ]:
                for alloc_policy in [
                    # '.aff-hybrid',
                    # '.aff-min-hops',
                    # '.aff-min-load',
                    '',
                    # '-random',
                    # '.aff-delta',
                ]:
                    sim = f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-rmt-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
                    tdg_folder = f'fake.0.tdg.{sim_input}{alloc_policy}.thread64'
                    out_fn = f'{result_prefix}/{conference}.{abbrev}{alloc_policy}.nest{nest}'
                    configurations.append({
                        'suite': suite,
                        'benchmark': benchmark,
                        'tdg_folder': tdg_folder,
                        'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                        'keyword': keyword,
                        'simulation': sim,
                        'out_fn': out_fn,
                    })

    if subset in ['bfs-push']:
        for nest in [
            16,
        ]:
            sim = f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-rmt-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
            for suite, benchmark, abbrev, sim_input, keyword in [
                ('gap', 'bfs_push_adj_uno_aff_sf', 'bfs_push_adj', 'krn17-k16-rnd64', 'swap.at'),
            ]:
                for alloc_policy in [
                    'hybrid5',
                    'min-hops',
                    'min-load',
                    'random',
                ]:
                    tdg_folder = f'fake.0.tdg.{sim_input}.aff-{alloc_policy}.thread64'
                    out_fn = f'{result_prefix}/{conference}.{abbrev}.{alloc_policy}.nest{nest}'
                    configurations.append({
                        'suite': suite,
                        'benchmark': benchmark,
                        'tdg_folder': tdg_folder,
                        'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                        'keyword': keyword,
                        'simulation': sim,
                        'out_fn': out_fn,
                        'interval': 10000,
                    })

    if subset in ['llc-cmp']:
        for nest in [
            16,
        ]:
            sim = f'{sim_prefix}-nest{nest}.fltsc-cmp-mif8-snuca1-rmt-strand0-ind0-b0.2-csr1-iacer0x0x0x0x0'
            for suite, benchmark, abbrev, sim_input, keyword in [
                ('gap', 'bfs_push_adj_uno_aff_sf', 'bfs_push_adj', 'krn17-k16-rnd64', 'LLC_SE'),
            ]:
                for alloc_policy in [
                    'hybrid5',
                    'min-hops',
                    'random',
                ]:
                    tdg_folder = f'fake.0.tdg.{sim_input}.aff-{alloc_policy}.thread64'
                    out_fn = f'{result_prefix}/{conference}.{subset}.{abbrev}.{alloc_policy}.nest{nest}'
                    configurations.append({
                        'suite': suite,
                        'benchmark': benchmark,
                        'tdg_folder': tdg_folder,
                        'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                        'keyword': keyword,
                        'simulation': sim,
                        'out_fn': out_fn,
                        'interval': 1000,
                    })

    return configurations

def collect(config):
    suite = config['suite']
    benchmark = config['benchmark']
    transform_name = config['transform']
    simulation = config['simulation']
    tdg_folder = config['tdg_folder']
    keyword = config['keyword']
    out_fn = config['out_fn']
    result_path = os.path.join(C.GEM_FORGE_RESULT_PATH, suite, benchmark, transform_name, simulation, tdg_folder)
    if 'interval' in config:
        interval = config['interval']
        interval_args = f'--interval={interval}'
    else:
        interval_args = f'--n-intervals=100'
    try:
        args = [
            f'{result_path}/stream_float_trace',
            interval_args,
            f'--align',
            f'--keyword={keyword}',
            f'--out-fn={out_fn}',
            f'--no-summary',
        ]
        StreamFloatTraceReader.main(args)
        result = 0
    except Exception as e:
        print(e)
        print('Failed {s} {b} {t} {sim} {tdg_folder}'.format(
            s=suite, b=benchmark, t=transform_name, sim=simulation, tdg_folder=tdg_folder))
        result = None
    return result


def main(subset):
    pool = multiprocessing.Pool(processes=32)
    jobs = []

    configurations = getConfigurations(subset)

    for config in configurations:
        jobs.append(pool.apply_async(
            collect,
            (config,)))

    failed = False
    for job in jobs:
        result = job.get()
        if result is None:
            failed = True

    if failed:
        print('Failed')
        return

if __name__ == '__main__':
    Util.mkdir_chain(result_prefix)
    import sys
    subset = sys.argv[1] if len(sys.argv) >= 2 else 'all'
    main(subset)
