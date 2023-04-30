
from BenchmarkDrivers.Benchmark import Benchmark
from BenchmarkDrivers.Benchmark import BenchmarkArgs

from Utils import TransformManager
from Utils import Gem5ConfigureManager
from Utils import TraceFlagEnum

import Constants as C
import Util

import os


class GAPGraphBenchmark(Benchmark):
    def __init__(self, benchmark_args, src_path, benchmark_name):
        self.cwd = os.getcwd()
        self.src_path = src_path
        self.benchmark_name = benchmark_name
        self.source = os.path.join('src', self.benchmark_name + '.cc')

        self.n_thread = benchmark_args.options.input_threads

        # Create the result dir out of the source tree.
        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, 'gap', self.benchmark_name
        )
        Util.mkdir_chain(self.work_path)

        super(GAPGraphBenchmark, self).__init__(benchmark_args)

    def get_name(self):
        return 'gap.{b}'.format(b=self.benchmark_name)

    def get_links(self):
        """
        Dynamic link still not work.
        """
        return [
            # '-fopenmp',
            # f'-L{C.AFFINITY_ALLOC_LIB_PATH}',
            # f'-lAffinityAllocGemForge',
            '-lomp',
            '-lpthread',
            '-Wl,--no-as-needed',
            '-ldl',
            f'-L{C.AFFINITY_ALLOC_LIB_PATH}',
            f'-lAffinityAllocGemForgeStatic',
        ]

    def get_args(self, input_name):
        graphs = os.path.join(self.src_path, 'benchmark/graphs')
        suffix = '.sg'
        graph_name, input_options = self.decompose_input_name(input_name)
        if self.benchmark_name.startswith('sssp') or self.benchmark_name.startswith('warm_weight'):
            suffix = '.wsg'
        graph_fn = os.path.join(graphs, graph_name + suffix)
        args = [
            '-f', graph_fn,
            '-p', str(self.n_thread),
            # Only one trial.
            '-n', '1',
        ]
        for opt in input_options:
            if opt == 'part':
                # Enable partition of the graph.
                args += [
                    '-j',
                ]
        cold_inputs = [
            ('krn21-k8', 1), # 2097152 Nodes (8MB w. 4B key), 16208491 undirected edges (126MB w. 4B key) for degree: 7.72881
            ('krn19-k16', 0),
            ('roadNet-PA', 0), # 1090920 Nodes (4.3MB w. 4B key), 3083796 edges (12MB w. 4B key)
            ('roadNet-TX', 0), # 1393383 Nodes (5.4MB w. 4B key), 3843320 edges (15MB w. 4B key)
            ('roadNet-CA', 0), # 1971281 Nodes (7.7MB w. 4B key), 5533214 edges (21.6MB w. 4B key)
            ('web-BerkStan', 0),
            ('road-great-britain-osm', 1), # 7733822 Nodes (30.2MB w. 4B key), 8156517 edges (31.9MB w. 4B key)
            ('soc-LiveJournal1', 1), # 4847571 Nodes (19MB w. 4B key) and 68475391 directed edges (267MB w. 4B key) for degree: 14.1257
            ('soc-pokec-relationships', 0),
        ]
        for i, c in cold_inputs:
            if graph_name == i:
                """
                This should be mix-level offloading, only warm up with
                specific level:
                0: Do not warm up.
                1: Warm up except the edge list.
                2: Warm up everything (default behavior).
                """
                args += [
                    '-c',
                    f'{c}',
                ]
                break
            if 'cold' in input_options:
                """
                Specifically disable warming.
                """
                args += [
                    '-c',
                    '0',
                ]
                break
        # SSSP need specific delta for some graphs to be able to finish.
        sssp_delta = {
            'road-great-britain-osm': 200,
        }
        if self.benchmark_name.startswith('sssp') and graph_name in sssp_delta:
            delta = sssp_delta[graph_name]
            args += [
                '-d',
                f'{delta}',
            ]
        return args

    def get_extra_compile_flags(self):
        return list()

    def get_sim_input_name(self, sim_input):
        return f'{sim_input}.thread{self.n_thread}'

    ADJ_WARM = 'omp?AdjListGraph<int, int, 0, 4, 64, true, true, (AdjListTypeE)0>::warmOneAdjListPerNode'
    S_ADJ_WARM = 'omp?AdjListGraph<int, int, 0, 4, 64, false, true, (AdjListTypeE)0>::warmOneAdjListPerNode'
    UNO_ADJ_WARM = 'AdjListGraph<int, int, 0, 4, 64, false, false, (AdjListTypeE)1>::warmSingleAdjList'
    MIX_ADJ_WARM = 'AdjListGraph<int, int, 0, 4, 64, false, true, (AdjListTypeE)3>::warmOneAdjListPerNode'
    W_UNO_ADJ_WARM = 'AdjListGraph<int, NodeWeight<int, int>, 4, 4, 64, false, false, (AdjListTypeE)1>::warmSingleAdjList'

    PR_PUSH_KERNEL_1_CSR = 'omp?pageRankPushCSR'
    PR_PUSH_KERNEL_1_ADJ = 'omp?pageRankPushAdjList'
    PR_PUSH_KERNEL_1_UNO_ADJ = 'omp?pageRankPushSingleAdjList'
    PR_PUSH_KERNEL_1_MIX_ADJ = 'omp?pageRankPushAdjListMixCSR'
    PR_PUSH_KERNEL_2 = 'omp?pageRankPushUpdate'
    PR_PUSH_KERNEL_INTER_PART = 'omp?pageRankPushInterPartUpdate'

    PR_PULL_KERNEL_1 = 'omp?pageRankPullUpdate'
    PR_PULL_KERNEL_2_CSR = 'omp?pageRankPullCSR'
    PR_PULL_KERNEL_2_ADJ = 'omp?pageRankPullAdjList'
    PR_PULL_KERNEL_2_UNO_ADJ = 'omp?pageRankPullSingleAdjList'

    PR_ADJ_WARM = 'omp?AdjListGraph<int, int, 0, 4, 64, true, true, (AdjListTypeE)0>::warmOneAdjListPerNode'
    PR_UNO_ADJ_WARM = 'AdjListGraph<int, int, 0, 4, 64, false, false, (AdjListTypeE)1>::warmSingleAdjList'

    BFS_PUSH_KERNEL = 'omp?bfsPushCSR'
    BFS_PUSH_ADJ_KERNEL = 'omp?bfsPushAdjList'
    BFS_PUSH_UNO_ADJ_KERNEL = 'omp?bfsPushSingleAdjList'
    BFS_ADJ_WARM = 'omp?AdjListGraph<int, int, 0, 4, 64, true, true, (AdjListTypeE)0>::warmOneAdjListPerNode'
    BFS_UNO_ADJ_WARM = 'AdjListGraph<int, int, 0, 4, 64, false, false, (AdjListTypeE)1>::warmSingleAdjList'

    BFS_PULL_KERNEL_1 = 'omp?bfsPullCSR'
    BFS_PULL_KERNEL_2 = 'omp?bfsPullUpdate'
    BFS_PULL_KERNEL_1_ADJ = 'omp?bfsPullAdjList'
    BFS_PULL_KERNEL_1_UNO_ADJ = 'omp?bfsPullSingleAdjList'

    SSSP_KERNEL = '.omp_outlined..22'
    SSSP_SPATIAL_KERNEL = '.omp_outlined..24'
    SSSP_SPATIAL_SF_KERNEL = 'omp?DeltaStepImpl'
    SSSP_ADJ_SPATIAL_SF_KERNEL = 'omp?DeltaStepImpl'
    SSSP_ADJ_SPATIAL_SF_WARM = '.omp_outlined..52'

    GRAPH_FUNC = {
        'bc':  ['.omp_outlined.', '.omp_outlined..13'],  # Two kernels
        # Two kernels -- top down and bottom up.
        'bfs': ['.omp_outlined.', '.omp_outlined..10', 'BUStep', 'DOBFS'],
        'bfs_push': [BFS_PUSH_KERNEL],
        'bfs_push_check': [BFS_PUSH_KERNEL],
        'bfs_push_offset': [BFS_PUSH_KERNEL],
        'bfs_push_spatial': [BFS_PUSH_KERNEL, 'gf_warm_impl'],
        'bfs_push_spatial_dyn128': [BFS_PUSH_KERNEL],
        'bfs_push_spatial_dyn256': [BFS_PUSH_KERNEL],
        'bfs_push_spatial_dyn512': [BFS_PUSH_KERNEL],
        'bfs_push_spatial_guided': [BFS_PUSH_KERNEL],
        'bfs_push_sf': [BFS_PUSH_KERNEL, 'gf_warm_impl'],
        'bfs_push_adj_rnd_spatial': [BFS_PUSH_ADJ_KERNEL, 'gf_warm_impl'],
        'bfs_push_adj_rnd_sf': [BFS_PUSH_ADJ_KERNEL, 'gf_warm_impl'],
        'bfs_push_adj_aff_sf': [BFS_PUSH_ADJ_KERNEL, BFS_ADJ_WARM, 'gf_warm_impl'],
        'bfs_push_adj_uno_aff_sf': [BFS_PUSH_UNO_ADJ_KERNEL, BFS_UNO_ADJ_WARM, 'gf_warm_impl'],

        'bfs_pull': [BFS_PULL_KERNEL_1, BFS_PULL_KERNEL_2], 
        'bfs_pull_nobrk': [BFS_PULL_KERNEL_1, BFS_PULL_KERNEL_2], 
        'bfs_pull_adj_aff': [BFS_PULL_KERNEL_1_ADJ, BFS_PULL_KERNEL_2], 
        'bfs_pull_adj_uno_aff': [BFS_PULL_KERNEL_1_UNO_ADJ, BFS_PULL_KERNEL_2], 
        'bfs_pull_nobrk_adj_aff': [BFS_PULL_KERNEL_1_ADJ, BFS_PULL_KERNEL_2], 
        'bfs_pull_shuffle': [BFS_PULL_KERNEL_1, BFS_PULL_KERNEL_2],  # Two kernels.
        'bfs_pull_shuffle_offset': [BFS_PULL_KERNEL_1, BFS_PULL_KERNEL_2],  # Two kernels.

        'pr_pull':  [PR_PULL_KERNEL_1, PR_PULL_KERNEL_2_CSR], 
        'pr_pull_adj_aff':  [PR_PULL_KERNEL_1, PR_PULL_KERNEL_2_ADJ, PR_ADJ_WARM], 
        'pr_pull_adj_uno_aff':  [PR_PULL_KERNEL_1, PR_PULL_KERNEL_2_UNO_ADJ, PR_UNO_ADJ_WARM],
        'pr_pull_shuffle':  [PR_PULL_KERNEL_1, PR_PULL_KERNEL_2_CSR],  # Two kernels
        'pr_pull_shuffle_offset':  [PR_PULL_KERNEL_1, PR_PULL_KERNEL_2_CSR],  # Two kernels

        'pr_push':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2, PR_PUSH_KERNEL_INTER_PART],
        'pr_push_adj_rnd':  [PR_PUSH_KERNEL_1_ADJ, PR_PUSH_KERNEL_2, ADJ_WARM],
        'pr_push_adj_lnr':  [PR_PUSH_KERNEL_1_ADJ, PR_PUSH_KERNEL_2, ADJ_WARM],
        'pr_push_adj_aff':  [PR_PUSH_KERNEL_1_ADJ, PR_PUSH_KERNEL_2, ADJ_WARM],
        'pr_push_adj_s_aff':  [PR_PUSH_KERNEL_1_ADJ, PR_PUSH_KERNEL_2, S_ADJ_WARM],
        'pr_push_adj_uno_aff':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_thd':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn16':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn32':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn64':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn128':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn256':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn512':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_uno_aff_dyn1024':  [PR_PUSH_KERNEL_1_UNO_ADJ, PR_PUSH_KERNEL_2, UNO_ADJ_WARM],
        'pr_push_adj_mix1_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix2_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix4_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix8_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix16_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix32_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_adj_mix64_aff':  [PR_PUSH_KERNEL_1_MIX_ADJ, PR_PUSH_KERNEL_2, MIX_ADJ_WARM],
        'pr_push_dyn':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_offset_dyn':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_offset_dyn_gap28kB':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_offset':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_offset_gap28kB':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_double':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_double_dyn':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_shuffle_double':  [PR_PUSH_KERNEL_1_CSR, PR_PUSH_KERNEL_2],  # Two kernels.
        'pr_push_inter_part':  [PR_PUSH_KERNEL_INTER_PART],
        'pr_push_atomic':  [PR_PUSH_KERNEL_1_CSR],  # One kernel.
        'pr_push_atomic_dyn':  [PR_PUSH_KERNEL_1_CSR],  # One kernel.
        'pr_push_atomic_double_dyn':  [PR_PUSH_KERNEL_1_CSR],  # One kernel.
        'pr_push_swap':  [PR_PUSH_KERNEL_1_CSR],  # One kernel.

        'sssp_outline': ['RelaxEdges'],
        'sssp_check': ['RelaxEdges'],
        'sssp': [SSSP_KERNEL],
        'sssp_sq_delta1': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sq_delta2': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sq_delta4': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sq_delta8': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sq_delta16': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sq_delta32': [SSSP_SPATIAL_KERNEL, 'copySpatialQueueToGlobalFrontier', 'gf_warm_impl'],
        'sssp_sf_delta1': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_sf_delta2': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_sf_delta4': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_sf_delta8': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_sf_delta16': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_sf_delta32': [SSSP_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta1': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta2': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta4': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta8': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta16': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_rnd_sf_delta32': [SSSP_ADJ_SPATIAL_SF_KERNEL, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta1':  [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta2':  [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta4':  [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta8':  [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta16': [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_aff_sf_delta32': [SSSP_ADJ_SPATIAL_SF_KERNEL, SSSP_ADJ_SPATIAL_SF_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_adj_uno_aff_sf_delta1':  [SSSP_ADJ_SPATIAL_SF_KERNEL, W_UNO_ADJ_WARM, 'copySpatialQueueToSpatialFrontier', 'gf_warm_impl'],
        'sssp_inline_offset': [SSSP_KERNEL],
        'tc':  ['.omp_outlined.'],

        'warm_weight':       ['gf_warm_impl'],  
        'warm_weight_adj':   ['gf_warm_impl', '.omp_outlined..38'],
        'warm_unweight':     ['gf_warm_impl'],
        'warm_unweight_adj': ['gf_warm_impl', '.omp_outlined..38'],
    }

    def get_trace_func(self):
        return Benchmark.ROI_FUNC_SEPARATOR.join(GAPGraphBenchmark.GRAPH_FUNC[self.benchmark_name])

    def get_lang(self):
        return 'CPP'

    def get_exe_path(self):
        return self.work_path

    def get_run_path(self):
        return self.work_path

    def get_profile_roi(self):
        return TraceFlagEnum.GemForgeTraceROI.SpecifiedFunction.value

    def build_raw_bc(self):
        os.chdir(self.src_path)
        bc = os.path.join(self.work_path, self.get_raw_bc())
        # Disable the loop unswitch to test for fault_stream.
        # Default no AVX512
        flags = [
            '-mllvm',
            '-loop-unswitch-threshold=1',
            '-mllvm',
            '-enable-load-pre=true',
            '-std=c++11',
            '-O3',
            '-Wall',
            '-fopenmp',
            '-DGEM_FORGE',
            '-DGEM_FORGE_WARM_CACHE',
            '-stream-specialize',
            # '-mllvm',
            # '-opt-bisect-limit=400',
        ]
        no_unroll_workloads = [
            'bfs_pull',
            'bfs_push',
            'pr_pull',
        ]
        for b in no_unroll_workloads:
            if self.benchmark_name.startswith(b):
                flags.append('-fno-unroll-loops')
                break
        if self.benchmark_name.startswith('pr_push'):
            flags.append('-ffast-math')
            flags.append('-fno-unroll-loops')
            flags.append('-mavx512f')

        sources = [self.source]
        bcs = [s[:-2] + '.bc' for s in sources]
        for source, bytecode in zip(sources, bcs):
            compile_cmd = [
                C.CXX,
                source,
                '-c',
            ] + flags + [
                '-emit-llvm',
                '-gline-tables-only',
                f'-I{C.GEM5_INCLUDE_DIR}',
                f'-I{C.AFFINITY_ALLOC_INC_PATH}',
                '-o',
                bytecode,
            ]
            Util.call_helper(compile_cmd)
        # Link into a single bc.
        Util.call_helper(['llvm-link', '-o', bc] + bcs)
        # Remove the bcs.
        Util.call_helper(['rm'] + bcs)
        # Remember to name every instruction.
        Util.call_helper([C.OPT, '-instnamer', bc, '-o', bc])
        Util.call_helper([C.LLVM_DIS, bc])

        self.post_build_raw_bc(bc)

        os.chdir(self.cwd)

    def get_additional_transform_options(self):
        return list()

    def trace(self):
        os.chdir(self.work_path)
        self.build_trace(
            trace_reachable_only=False,
        )
        # For this benchmark, we only trace the target function.
        os.putenv('LLVM_TDG_TRACE_MODE', str(
            TraceFlagEnum.GemForgeTraceMode.TraceAll.value))
        os.putenv('LLVM_TDG_TRACE_ROI', str(
            TraceFlagEnum.GemForgeTraceROI.SpecifiedFunction.value))
        self.run_trace()
        os.chdir(self.cwd)

    def get_additional_gem5_simulate_command(self, transform_config, simulation_config, input_name):

        additional_options = list()

        """
        To reduce simulation time, here I charge 4000ns yield latency.
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.
        """
        additional_options += [
            "--cpu-yield-lat=4000ns",
        ]
        if self.benchmark_name.startswith('sssp'):
            additional_options.append(
                "--gem-forge-stream-engine-enable-float-history=0"
            )
        work_items = -1
        if self.benchmark_name.startswith('pr'):
            # Two kernels, two iteration.
            work_items = 4
            _, input_options = self.decompose_input_name(input_name)
            if 'iter=1' in input_options:
                work_items = 2
            elif 'iter=3' in input_options:
                work_items = 6
            for single_kernel_prefix in [
                'pr_push_atomic',
                'pr_push_swap',
            ]:
                if self.benchmark_name.startswith(single_kernel_prefix):
                    work_items = work_items // 2
                    break
        """
        This takes too long to finish. So we limit some work items.
        """
        input_benchmark_work_items = [
            ('road-great-britain-osm', 'sssp', 1000), # 1000 iters -> about 24 hours for NSC+Mem.
            ('road-great-britain-osm', 'bfs_push', 666), # 666 iters -> 24 hours for NSC+Mem.
        ]
        for i, b, w in input_benchmark_work_items:
            if input_name.startswith(i) and self.benchmark_name.startswith(b):
                work_items = w
                break
        if work_items != -1:
            additional_options.append(
                f'--work-end-exit-count={work_items}'
            )
        """
        To avoid the performance degrade after configuring the IndirectReductionStream
        in bfs_pull, bfs_pull_shuffle, pr_pull, pr_pull_shuffle, we increment the
        default CoreSE FIFO entries from 128 to 136.
        """
        pull_benchmarks = {
            'bfs_pull': 192,
            'bfs_pull_shuffle': 192,
            'pr_pull': 160,
            'pr_pull_shuffle': 160,
        }
        transform_id = transform_config.get_transform_id()
        simulation_id = simulation_config.get_simulation_id()
        if self.benchmark_name in pull_benchmarks:
            if transform_id.startswith('stream.ex.static.so.store.cmp'):
                entries = pull_benchmarks[self.benchmark_name]
                additional_options.append(
                    f'--gem-forge-stream-engine-total-run-ahead-length={entries}',
                )
                if 'fltsc-cmp-' in simulation_id:
                    additional_options.append(
                        '--gem-forge-enable-stream-float-indirect-reduction',
                    )
        return additional_options

    def get_gem5_mem_size(self):
        return '4GB'


class GAPGraphSuite:

    def __init__(self, benchmark_args):
        benchmark_path = os.getenv('GEM_FORGE_BENCHMARK_PATH')
        if benchmark_path is None:
            print('Please specify where the benchmark is in GEM_FORGE_BENCHMARK_PATH')
            assert(False)
        suite_folder = os.path.join(benchmark_path, 'gapbs')
        self.benchmarks = list()
        for name in GAPGraphBenchmark.GRAPH_FUNC:
            benchmark_name = 'gap.{n}'.format(n=name)
            if benchmark_args.options.benchmark:
                if benchmark_name not in benchmark_args.options.benchmark:
                    # Ignore benchmark not required.
                    continue
            self.benchmarks.append(GAPGraphBenchmark(
                benchmark_args, suite_folder, name))

    def get_benchmarks(self):
        return self.benchmarks
