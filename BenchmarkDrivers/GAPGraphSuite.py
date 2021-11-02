
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
        return [
            '-lomp',
            '-lpthread',
            '-Wl,--no-as-needed',
            '-ldl',
        ]

    def get_args(self, input_name):
        graphs = os.path.join(self.src_path, 'benchmark/graphs')
        suffix = '.sg'
        if self.benchmark_name.startswith('sssp'):
            suffix = '.wsg'
        graph_fn = os.path.join(graphs, input_name + suffix)
        args = [
            '-f', graph_fn,
            '-p', str(self.n_thread),
            # Only one trial.
            '-n', '1',
        ]
        if input_name.startswith('krn21-k8') or input_name.startswith('krn19-k16'):
            # This should be mix-level offloading, do not warm up cache.
            args += [
                '-c'
            ]
        return args

    def get_extra_compile_flags(self):
        return list()

    def get_sim_input_name(self, sim_input):
        return f'{sim_input}-thread{self.n_thread}'

    GRAPH_FUNC = {
        'bc':  ['.omp_outlined.', '.omp_outlined..13'],  # Two kernels
        # Two kernels -- top down and bottom up.
        'bfs': ['.omp_outlined.', '.omp_outlined..10', 'BUStep', 'DOBFS'],
        'bfs_push': ['.omp_outlined.'],
        'bfs_push_check': ['.omp_outlined.'],
        'bfs_pull': ['.omp_outlined.', '.omp_outlined..10'],  # Two kernels.
        'bfs_pull_shuffle': ['.omp_outlined.', '.omp_outlined..11'],  # Two kernels.
        'pr_pull':  ['.omp_outlined..12', '.omp_outlined..13'],  # Two kernels.
        'pr_pull_shuffle':  ['.omp_outlined..13', '.omp_outlined..14'],  # Two kernels.
        'pr_push':  ['.omp_outlined..18', '.omp_outlined..19'],  # Two kernels.
        'pr_push_double':  ['.omp_outlined..18', '.omp_outlined..19'],  # Two kernels.
        'pr_push_shuffle_double':  ['.omp_outlined..18', '.omp_outlined..19'],  # Two kernels.
        'pr_push_atomic':  ['.omp_outlined..18'],  # One kernel.
        'pr_push_swap':  ['.omp_outlined..18'],  # One kernel.
        'sssp': ['RelaxEdges'],
        'sssp_check': ['RelaxEdges'],
        'tc':  ['.omp_outlined.'],
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
            # '-opt-bisect-limit=3410',
        ]
        no_unroll_workloads = [
            'bfs',
            'bfs_pull',
            'bfs_pull_shuffle',
            'bfs_push',
            'bfs_push_check',
            'pr_pull',
            'pr_pull_shuffle',
        ]
        if self.benchmark_name in no_unroll_workloads:
            flags.append('-fno-unroll-loops')
        if self.benchmark_name.startswith('pr_push'):
            flags.append('-ffast-math')
            flags.append('-fno-unroll-loops')
            # flags.append('-mavx512f')

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
                '-I{INCLUDE}'.format(INCLUDE=C.GEM5_INCLUDE_DIR),
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
        """
        To reduce simulation time, here I charge 4000ns yield latency.
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.
        """
        additional_options = [
            "--cpu-yield-lat=4000ns",
        ]
        work_items = -1
        if self.benchmark_name.startswith('pr'):
            # Two kernels, two iteration.
            if self.benchmark_name in ['pr_push_atomic', 'pr_push_swap']:
                work_items = 2
            else:
                work_items = 4
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
        return '1GB'


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
