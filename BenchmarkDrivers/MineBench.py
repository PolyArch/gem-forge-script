from BenchmarkDrivers.Benchmark import Benchmark
from BenchmarkDrivers.Benchmark import BenchmarkArgs

from Utils import TransformManager
from Utils import Gem5ConfigureManager
from Utils import TraceFlagEnum

import Constants as C
import Util

import os

class MineBenchmark(Benchmark):

    ARGS = {
        'svm': {
            'tiny': ['$NTHREADS', '8_1024.data', '1024', '8', '2'],
            'test': ['$NTHREADS', '8_16384.data', '16384', '8', '2'],
            'medium': ['$NTHREADS', '8_131072.data', '131072', '8', '2'],
            'large': ['$NTHREADS', '8_390216.data', '390216', '8', '2'],
            # 'large': ['$NTHREADS', '8_786432.data', '786432', '8', '2'],
        },
    }

    ROI_FUNCS = {
        'svm': [
            '.omp_outlined..11', # SVC_Q::get_Q.
        ],
    }

    """
    For some benchmarks, it takes too long to finish the large input set.
    We limit the number of work items here, by limiting the number of 
    microops to be roughly 1e8.
    """
    WORK_ITEMS = {
        'svm': 1,  # Try one iteration?
    }

    def __init__(self, benchmark_args, benchmark_path):
        self.cwd = os.getcwd()
        self.benchmark_path = benchmark_path
        self.benchmark_name = os.path.basename(self.benchmark_path)

        self.n_thread = benchmark_args.options.input_threads

        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, 'mine', self.benchmark_name
        )
        Util.mkdir_chain(self.work_path)
        super(MineBenchmark, self).__init__(benchmark_args)

    def get_name(self):
        return 'mine.{b}'.format(b=self.benchmark_name)

    def get_links(self):
        return [
            '-lm',
            '-lomp',
            '-lpthread',
            '-Wl,--no-as-needed',
            '-ldl',
        ]

    def get_gem5_links(self):
        return [
            '-lopenlibm',
            '-lomp',
            '-lpthread',
            '-Wl,--no-as-needed',
            '-ldl',
        ]

    def get_trace_func(self):
        if self.benchmark_name in MineBenchmark.ROI_FUNCS:
            roi_funcs = MineBenchmark.ROI_FUNCS[self.benchmark_name]
            return Benchmark.ROI_FUNC_SEPARATOR.join(
                roi_funcs
            )
        return None

    def _get_args(self, input_name):
        data_folder = os.path.join(
            self.benchmark_path,
            '../../data',
            self.benchmark_name,
        )
        args = list()
        for arg in MineBenchmark.ARGS[self.benchmark_name][input_name]:
            if arg == '$NTHREADS':
                args.append(str(self.n_thread))
            else:
                args.append(arg.format(DATA=data_folder))
        return args

    def get_args(self, input_name):
        return self._get_args(input_name)

    def get_extra_compile_flags(self):
        if 'avx' in self.benchmark_name:
            return ['-mavx512f']
        return list()

    def get_sim_input_args(self, input_name):
        return self._get_args(input_name)

    def get_sim_input_name(self, input_name):
        return f'{input_name}-thread{self.n_thread}'

    def get_lang(self):
        return 'CPP'

    def get_exe_path(self):
        return self.benchmark_path

    def get_sim_exe_path(self):
        return self.benchmark_path

    def get_run_path(self):
        return self.work_path

    def get_additional_gem5_simulate_command(self, transform_config, simulation_config):
        """
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.
        """
        flags = [
            "--cpu-yield-lat=4000ns",
        ]
        work_items = MineBenchmark.WORK_ITEMS[self.benchmark_name]
        if work_items != -1:
            flags.append(
                '--work-end-exit-count={v}'.format(v=work_items)
            )
        return flags

    def build_raw_bc(self):
        os.chdir(self.benchmark_path)
        make_cmd = [
            'make',
            '-f',
            'Makefile',
        ]
        clean_cmd = make_cmd + [
            'clean',
        ]
        Util.call_helper(clean_cmd)
        build_cmd = make_cmd + [
            'raw.bc',
        ]
        Util.call_helper(build_cmd)
        # Copy to the work_path
        cp_cmd = [
            'cp',
            self.get_raw_bc(),
            self.get_run_path(),
        ]
        Util.call_helper(cp_cmd)
        os.chdir(self.cwd)

    def trace(self):
        os.chdir(self.get_exe_path())
        self.build_trace(
            trace_reachable_only=False,
        )

        # This benchmark should not be really traced.
        assert(self.options.fake_trace)
        self.run_trace()

        os.chdir(self.cwd)


class MineSuite:
    def __init__(self, benchmark_args):
        benchmark_path = os.getenv('GEM_FORGE_BENCHMARK_PATH')
        if benchmark_path is None:
            print('Please specify where the benchmark is in GEM_FORGE_BENCHMARK_PATH')
            assert(False)
        suite_folder = os.path.join(benchmark_path, 'MineBench')
        self.benchmarks = list()
        sub_folders = ['.']
        for sub_folder in sub_folders:
            items = os.listdir(os.path.join(suite_folder, sub_folder))
            items.sort()
            for item in items:
                if item[0] == '.':
                    # Ignore special folders.
                    continue
                if item not in MineBenchmark.ARGS:
                    continue
                benchmark_name = 'mine.{b}'.format(b=os.path.basename(item))
                if benchmark_args.options.benchmark:
                    if benchmark_name not in benchmark_args.options.benchmark:
                        # Ignore benchmark not required.
                        continue
                abs_path = os.path.join(suite_folder, sub_folder, item)
                if os.path.isdir(abs_path):
                    self.benchmarks.append(
                        MineBenchmark(benchmark_args, abs_path))

    def get_benchmarks(self):
        return self.benchmarks
