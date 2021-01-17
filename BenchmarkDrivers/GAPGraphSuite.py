
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
        self.sim_input_name = benchmark_args.options.sim_input_name

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

    def get_args(self):
        graphs = os.path.join(self.src_path, 'benchmark/graphs')
        suffix = '.sg'
        if self.benchmark_name == 'sssp':
            suffix = '.wsg'
        graph_fn = os.path.join(graphs, self.sim_input_name + suffix)
        args = [
            '-f', graph_fn,
            '-p', str(self.n_thread),
            # Only one trial.
            '-n', '1',
        ]
        return args

    def get_extra_compile_flags(self):
        return list()

    def get_sim_input_name(self):
        return self.sim_input_name

    GRAPH_FUNC = {
        'bc':  ['.omp_outlined.', '.omp_outlined..13'],  # Two kernels
        # Two kernels -- top down and bottom up.
        'bfs': ['.omp_outlined.', '.omp_outlined..10', 'BUStep', 'DOBFS'],
        'pr_pull':  ['.omp_outlined.', '.omp_outlined..10'],  # Two kernels.
        'pr_push':  ['.omp_outlined..12', '.omp_outlined..13'],  # Two kernels.
        'sssp': ['RelaxEdges'],
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
        ]
        no_unroll_workloads = [
            'bfs',
            'pr_pull',
            'pr_push',
        ]
        if self.benchmark_name in no_unroll_workloads:
            flags.append('-fno-unroll-loops')
            flags.append('-fno-vectorize')

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

    def get_additional_gem5_simulate_command(self):
        """
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.
        """
        work_items = -1
        if self.benchmark_name.startswith('pr'):
            # Two kernels, two iteration.
            work_items = 4
        if work_items == -1:
            # This benchmark can finish.
            return list()
        return [
            '--work-end-exit-count={v}'.format(v=work_items)
        ]

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
