from BenchmarkDrivers.Benchmark import Benchmark
from BenchmarkDrivers.Benchmark import BenchmarkArgs

from Utils import TransformManager
from Utils import Gem5ConfigureManager
from Utils import TraceFlagEnum

import Constants as C
import Util

import os


class RodiniaBenchmark(Benchmark):

    ARGS = {
        # 'backprop': {
        #     'test': ['1024', '$NTHREADS'],
        #     'medium': ['16384', '$NTHREADS'],
        #     'large': ['65536', '$NTHREADS'],
        # },
        'b+tree': {
            'large': ['cores', '$NTHREADS', 'binary', 'file', '{DATA}/btree.data'],
        },
        'bfs': {
            'test': ['$NTHREADS',    '{DATA}/graph4096.txt.data'],
            'medium': ['$NTHREADS', '{DATA}/graph65536.txt.data'],
            'large': ['$NTHREADS',  '{DATA}/graph1MW_6.txt.data'],
        },
        'cfd': {
            'test':   ['{DATA}/fvcorr.domn.097K.data', '$NTHREADS'],
            'medium': ['{DATA}/fvcorr.domn.193K.data', '$NTHREADS'],
            'large':  ['{DATA}/fvcorr.domn.193K.data', '$NTHREADS'],
        },
        'hotspot': {
            # DataType(double), 3 Arrays.
            # rows, cols, iterations, threads, data(unused), power(unused), output(unused), warm
            'test':   ['64', '64', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'medium': ['512', '512', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'large':  ['2048', '1024', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'mix':    ['3584', '1024', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '0'],
        },
        'hotspot3D': {
            # DataType(double), 3 Arrays
            # rows, cols, layers, iters, threads, unused, unused, unused, warm,
            'test':   ['64', '64', '8', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'medium': ['512', '512', '2', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'large':  ['256', '1024', '8', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '1'],
            'mix':    ['512', '1024', '8', '100', '$NTHREADS', 'invalid.data', 'invalid.data', 'output.txt', '0'],
        },
        'kmeans': {
            'test':   ['-b', 'dummy', '-n', '$NTHREADS', '-i', '{DATA}/100.data'],
            'medium': ['-b', 'dummy', '-n', '$NTHREADS', '-i', '{DATA}/204800.txt.data'],
            'large':  ['-b', 'dummy', '-n', '$NTHREADS', '-i', '{DATA}/kdd_cup.data'],
        },
        'lavaMD': {
            'large':  ['-cores', '$NTHREADS', '-boxes1d', '16'],
        },
        'nw': {
            'test': ['128', '10', '$NTHREADS'],
            'medium': ['512', '10', '$NTHREADS'],
            'large': ['2048', '10', '$NTHREADS'],
        },
        'nw-blk32': {
            'large': ['2048', '10', '$NTHREADS'],
        },
        'nn': {
            'test': ['list4k.data.txt', '5', '30', '90', '$NTHREADS'],
            'medium': ['list16k.data.txt', '5', '30', '90', '$NTHREADS'],
            # 'large': ['list256k.data.txt', '5', '30', '90', '$NTHREADS'],
            'large': ['list768k.data.txt', '5', '30', '90', '$NTHREADS'],
        },
        'particlefilter': {
            'test':   ['-x', '100', '-y', '100', '-z', '10', '-np', '100', '-nt', '$NTHREADS'],
            'medium': ['-x', '100', '-y', '100', '-z', '10', '-np', '1000', '-nt', '$NTHREADS'],
            # 'large':  ['-x', '100', '-y', '100', '-z', '10', '-np', '8196', '-nt', '$NTHREADS'],
            # 'large':  ['-x', '100', '-y', '100', '-z', '10', '-np', '12288', '-nt', '$NTHREADS'],
            'large':  ['-x', '1000', '-y', '1000', '-z', '10', '-np', '49152', '-nt', '$NTHREADS'],
            # 'large':  ['-x', '100', '-y', '100', '-z', '10', '-np', '32768', '-nt', '$NTHREADS'],
        },
        'pathfinder': {
            # cols, rows, threads, warm.
            'test': ['100', '100', '$NTHREADS', '1'],
            'medium': ['1000', '100', '$NTHREADS', '1'],
            'large': [str(6 * 1024 * 1024 // 4), '100', '$NTHREADS', '1'],
            'large-cold': [str(6 * 1024 * 1024 // 4), '100', '$NTHREADS', '0'],
            'mix': [str(24 * 1024 * 1024 // 4), '100', '$NTHREADS', '0'],
            'mem': [str(48 * 1024 * 1024 // 4), '100', '$NTHREADS', '0'],
        },
        'srad_v2': {
            # DataType(float), 6 arrays.
            # rows, cols, x0, x1, y0, y1, threads, lambda, iterations, warm.
            'medium': ['256', '2048', '0', '127', '0', '127', '$NTHREADS', '0.5', '100', '1'],
            'large': ['1024', '2048', '0', '127', '0', '127', '$NTHREADS', '0.5', '100', '1'],
            'mix': ['1536', '2048', '0', '127', '0', '127', '$NTHREADS', '0.5', '100', '0'],
        },
        'srad_v3': {
            # DataType(float), 3 arrays.
            # rows, cols, x0, x1, y0, y1, threads, lambda, iterations, warm.
            'large': ['2048', '2048', '0', '127', '0', '127', '$NTHREADS', '0.5', '100', '1'],
            'mix': ['4196', '2048', '0', '127', '0', '127', '$NTHREADS', '0.5', '100', '0'],
        },
        'streamcluster': {
            'tiny': ['10', '20', '16', '1024', '1024', '1000', '16_1024.data', 'output.txt', '$NTHREADS'],
            'test': ['10', '20', '16', '16384', '16384', '1000', '16_16384.data', 'output.txt', '$NTHREADS'],
            'medium': ['10', '20', '16', '131072', '131072', '1000', '16_131072.data', 'output.txt', '$NTHREADS'],
            'large': ['10', '20', '16', '786432', '786432', '1000', '16_786432.data', 'output.txt', '$NTHREADS'],
        },
    }

    ROI_FUNCS = {
        'b+tree': [
            '.omp_outlined..33',  # kernel_range
            '.omp_outlined..37',  # kernel_query
        ],
        'bfs': [
            '.omp_outlined.',
            '.omp_outlined..3',
        ],
        'cfd': [
            # '.omp_outlined.',   # initialize_variables()
            '.omp_outlined..5',  # compute_step_factor()
            '.omp_outlined..6',  # compute_flux()
            '.omp_outlined..7',  # time_step()
            '.omp_outlined..12',  # copy()
        ],
        'hotspot': [
            '.omp_outlined.',
        ],
        'hotspot3D': [
            '.omp_outlined.',
        ],
        'kmeans': [
            '.omp_outlined.',
            'kmeans_kernel',
        ],
        'lavaMD': [
            '.omp_outlined.',
        ],
        'nw': [
            '.omp_outlined.',
            '.omp_outlined..8',
        ],
        'nw-blk32': [
            '.omp_outlined.',
            '.omp_outlined..7',
        ],
        'nn': [
            '.omp_outlined..7',
            '.omp_outlined..8',
        ],
        'particlefilter': [
            '.omp_outlined.',  # applyMotionModel()
            '.omp_outlined..2',  # computeLikelihood()
            '.omp_outlined..4',  # updateWeight(): exp(likelihood) + sum(weights)
            '.omp_outlined..5',  # updateWeight(): normalize(weight)
            '.omp_outlined..7',  # averageParticles()
            'resampleParticles',  # resampleParticles(): compute(CDF)
            '.omp_outlined..11',  # resampleParticles(): compute(U)
            '.omp_outlined..13',  # resampleParticles(): resample
            '.omp_outlined..15',  # resampleParticles(): reset
        ],
        'pathfinder': [
            '.omp_outlined..3',
        ],
        'srad_v2': [
            'sumROI',
            '.omp_outlined..13',
            '.omp_outlined..14',
        ],
        'srad_v2-avx512-fix-kernel1': [
            'sumROI',
            '.omp_outlined..13',
        ],
        'srad_v2-avx512-fix-kernel2': [
            'sumROI',
            '.omp_outlined..13',
        ],
        'srad_v3': [
            'sumROI',
            '.omp_outlined..13',
            '.omp_outlined..14',
        ],
        'streamcluster': [
            'pgain_dist',
            'pgain_assign',
        ],
    }

    """
    For some benchmarks, it takes too long to finish the large input set.
    We limit the number of work items here, by limiting the number of 
    microops to be roughly 1e8.
    """
    WORK_ITEMS = {
        'b+tree': 2,  # Two commands.
        'bfs': 2 * int(1e8 / 15e5),  # One iter takes 15e5 ops.
        'cfd': 4 * int(1e8 / 2e7),
        'hotspot': 2,  # Two iters takes 10 min.
        'hotspot3D': 2, # Two iters.
        'kmeans': 3 * 1,
        'lavaMD': 1,            # Invoke kernel for once.
        'nw': 2,                # nw can finish.
        'nw-blk32': 2,                # nw can finish.
        'nn': 4,                # One iteration is 4 work items.
        'particlefilter': 9 * 1,  # One itertion is enough.
        'pathfinder': 7,        # pathfinder takes 7 iterations.
        'srad_v2': 2 * 1,  # One iteration is enough.
        'srad_v3': 2 * 1,  # One iteration is enough.
        'streamcluster': 4,  # Try one iteration?
    }

    def __init__(self, benchmark_args, benchmark_path):
        self.cwd = os.getcwd()
        self.benchmark_path = benchmark_path
        self.benchmark_name = os.path.basename(self.benchmark_path)

        self.n_thread = benchmark_args.options.input_threads

        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, 'rodinia', self.benchmark_name
        )
        self.benchmark_name_prefix = RodiniaBenchmark.get_name_prefix(self.benchmark_name)

        Util.mkdir_chain(self.work_path)
        super(RodiniaBenchmark, self).__init__(benchmark_args)

    @staticmethod
    def get_name_prefix(name):
        prefixes = [
            'hotspot',
            'hotspot3D',
            'pathfinder',
            'srad_v2',
            'srad_v3',
        ]
        for prefix in prefixes:
            if name.startswith(f'{prefix}-'):
                return prefix
        return name

    def get_name(self):
        return 'rodinia.{b}'.format(b=self.benchmark_name)

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
        if self.benchmark_name_prefix in RodiniaBenchmark.ROI_FUNCS:
            roi_funcs = RodiniaBenchmark.ROI_FUNCS[self.benchmark_name_prefix]
            return Benchmark.ROI_FUNC_SEPARATOR.join(
                roi_funcs
            )
        return None

    def break_input_name(self, input_name):
        """
        The input name is defined in "size-length"
        """
        fields = [input_name]
        if '-' in input_name:
            fields = input_name.split('-')
        while len(fields) < 3:
            fields.append(None)
        return fields

    def get_input_size(self, input_name):
        return self.break_input_name(input_name)[0]

    def _get_args(self, input_name):
        data_folder = os.path.join(
            self.benchmark_path,
            '../../data',
            self.benchmark_name,
        )
        input_size = self.get_input_size(input_name)
        args = list()
        for arg in RodiniaBenchmark.ARGS[self.benchmark_name_prefix][input_size]:
            if arg == '$NTHREADS':
                args.append(str(self.n_thread))
            else:
                args.append(arg.format(DATA=data_folder))
        return args

    def get_args(self, input_name):
        assert(False)
        return None

    def get_extra_compile_flags(self):
        if 'avx' in self.benchmark_name:
            return ['-mavx512f']
        return list()

    def get_sim_args(self, input_name):
        return self._get_args(input_name)

    def get_sim_input_name(self, sim_input):
        return f'{sim_input}-thread{self.n_thread}'

    def get_lang(self):
        return 'CPP'

    def get_exe_path(self):
        return self.benchmark_path

    def get_sim_exe_path(self):
        return self.benchmark_path

    def get_run_path(self):
        return self.work_path

    def get_additional_gem5_simulate_command(self, transform_config, simulation_config, input_name):
        """
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.

        Also, we control the number of iters for some workloads based on the input name.
        """
        flags = list()

        work_items = RodiniaBenchmark.WORK_ITEMS[self.benchmark_name_prefix]

        # Overwrite work items if the input required.
        var_work_item_base = {
            'hotspot': 1,
            'hotspot3D': 1,
            'pathfinder': 1,
            'srad_v2': 2,
            'srad_v3': 2,
        }
        var_work_item_time = {
            'one': 1,
            'two': 2,
            'short': 4,
            'long': 8,
        }
        input_name_fields = self.break_input_name(input_name)
        if input_name_fields[1] in var_work_item_time:
            if self.benchmark_name_prefix in var_work_item_base:
                work_item_bases = var_work_item_base[self.benchmark_name_prefix]
                work_item_times = var_work_item_time[input_name_fields[1]]
                work_items = work_item_bases * work_item_times
        if work_items != -1:
            flags.append(
                '--work-end-exit-count={v}'.format(v=work_items)
            )
        if self.benchmark_name == 'streamcluster':
            # Streamcluster uses pthread, which barrier may cause CPU 0 to wait for
            # a long when other thread is still working. So we disable deadlock check.
            flags.append(
                '--gem-forge-cpu-deadlock-interval=0ns'
            )
        return flags

    def build_raw_bc(self):
        os.chdir(self.benchmark_path)
        make_cmd = [
            'make',
            '-f',
            'GemForge.Makefile',
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


class RodiniaSuite:

    def search(self, benchmark_args, folder):
        if not os.path.isdir(folder):
            return
        items = os.listdir(folder)
        items.sort()
        for item in items:
            if item[0] == '.':
                # Ignore special folders.
                continue
            prefix = RodiniaBenchmark.get_name_prefix(item)
            if prefix not in RodiniaBenchmark.ARGS:
                # Search in subfolders.
                self.search(benchmark_args, os.path.join(folder, item))
                continue
            benchmark_name = 'rodinia.{b}'.format(b=os.path.basename(item))
            if benchmark_args.options.benchmark:
                if benchmark_name not in benchmark_args.options.benchmark:
                    # Search in subfolders.
                    self.search(benchmark_args, os.path.join(folder, item))
                    # Ignore benchmark not required.
                    continue
            abs_path = os.path.join(folder, item)
            if os.path.isdir(abs_path):
                self.benchmarks.append(
                    RodiniaBenchmark(benchmark_args, abs_path))

    def __init__(self, benchmark_args):
        benchmark_path = os.getenv('GEM_FORGE_BENCHMARK_PATH')
        if benchmark_path is None:
            print('Please specify where the benchmark is in GEM_FORGE_BENCHMARK_PATH')
            assert(False)
        suite_folder = os.path.join(benchmark_path, 'Rodinia')
        self.benchmarks = list()
        sub_folders = ['openmp']
        for sub_folder in sub_folders:
            self.search(benchmark_args, os.path.join(suite_folder, sub_folder))

    def get_benchmarks(self):
        return self.benchmarks


"""

b+tree:
Inner-most stream is enough.
[i.store]
[i.store] + [fltm]
[i.store.rdc] + [fltm]

bfs:
[so.store]
[so.store] + [fltmi]
[so.store.ipred] + [fltmi]
[so.store.rdc] + [fltmi]

hotspot/hotspot3D:
[so.store]
[so.store] + [flt]

nn:
Compute the nearest neighbor, but only the for loop to compute the distance is parallelized.
A lot of file IO in the ROI.
[i.store]
[i.store] + [fltm]
[i.store.ldst] + [fltm]

nw:
Needleman-Wunsch. The problem is that it is tiled for better temporal locality.
And inplace computing makes it frequently aliased.
[i.store]
[i.store] + [fltm]

cfd:
compute_step_factor.
compute_flux. (with indirect access).
time_step.

stream cluster:
Same as Parsec. So this should not work as there is a lot of file IO in the ROI.

leukocyte tracking:
It uses a separate matrix library also read in from a AVI file.

heart wall tracking:
It reads from an AVI file frame by frame in the ROI.

mummer-gpu:
Complicated. Seems to be optimized for gpu.

particlefilter
[so.store]
[so.store] + [fltm]

pathfinder:
[so.store]
[so.store] + [fltm]

srad_v2:
[so.store] + [fltm]

"""
