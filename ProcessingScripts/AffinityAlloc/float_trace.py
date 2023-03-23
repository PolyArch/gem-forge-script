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

StreamFloatTraceReader.enable_print = False

def getConfigurations(subset):

    configurations = list()

    sim_fmt = 'ss.ruby.uno.o8.8x8c-l256-c4-s1kB-ch4kB.f2048x256-c-gb-o3end-nest{nest}.fltsc-cmp-snuca-rmtcfg-strand0-ind64-b0.2-csr1-iace0x0x0x0'

    if subset in ['float-trace']:
        for suite, benchmark, abbrev, sim_input, keyword, nest, alloc_policy in [
            # ('gap', 'pr_push_adj_aff', 'fake.0.tdg.krn17-k16.aff-hybrid.thread64'),
            ('gfm', 'omp_link_list_search_aff', 'link-list', 'large', 'link_list.next.ld', 16, 'hybrid'),
            ('gfm', 'omp_link_list_search_aff', 'link-list', 'large', 'link_list.next.ld', 16, 'min-hops'),
            ('gfm', 'omp_link_list_search_aff', 'link-list', 'large', 'link_list.next.ld', 16, 'min-load'),
            ('gfm', 'omp_link_list_search_aff', 'link-list', 'large', 'link_list.next.ld', 16, 'random'),
            ('gfm', 'omp_hash_join_aff', 'hash-join', 'large', 'hash_join.next.ld', 16, 'hybrid'),
            ('gfm', 'omp_hash_join_aff', 'hash-join', 'large', 'hash_join.next.ld', 16, 'min-hops'),
            ('gfm', 'omp_hash_join_aff', 'hash-join', 'large', 'hash_join.next.ld', 16, 'min-load'),
            ('gfm', 'omp_hash_join_aff', 'hash-join', 'large', 'hash_join.next.ld', 16, 'random'),
        ]:
            tdg_folder = f'fake.0.tdg.{sim_input}.aff-{alloc_policy}.thread64'
            out_fn = f'{result_prefix}/{conference}.{abbrev}.{alloc_policy}.nest{nest}'
            configurations.append({
                'suite': suite,
                'benchmark': benchmark,
                'tdg_folder': tdg_folder,
                'transform': 'stream.ex.static.so.store.cmp-bnd-elim-nst',
                'keyword': keyword,
                'simulation': sim_fmt.format(nest=nest),
                'out_fn': out_fn,
            })

    return configurations

def collect(suite, benchmark, transform_name, simulation, tdg_folder, keyword, out_fn):
    result_path = os.path.join(C.GEM_FORGE_RESULT_PATH, suite, benchmark, transform_name, simulation, tdg_folder)
    try:
        args = [
            f'{result_path}/stream_float_trace',
            f'--n-intervals=100',
            f'--align',
            f'--keyword={keyword}',
            f'--out-fn={out_fn}',
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
        suite = config['suite']
        benchmark = config['benchmark']

        transform_name = config['transform']
        simulation = config['simulation']
        tdg_folder = config['tdg_folder']
        keyword = config['keyword']
        out_fn = config['out_fn']
        jobs.append(pool.apply_async(
            collect,
            (suite, benchmark, transform_name, simulation, tdg_folder, keyword, out_fn)))

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
