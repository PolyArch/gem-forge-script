
from BenchmarkDrivers.Benchmark import Benchmark
from BenchmarkDrivers.Benchmark import BenchmarkArgs

from Utils import TransformManager
from Utils import Gem5ConfigureManager
from Utils import TraceFlagEnum

import Constants as C
import Util

import os


class GemForgeMicroBenchmark(Benchmark):

    INPUT_SIZE = {
        'omp_partition_avx': {
            'large': ['large']
        },
        'omp_radix_partition_indirect_avx': {
            'large': ['large']
        },
        'omp_link_list_search': {
            # nodes per list, num of lists.
            'test': [str(64), str(64)],
            'small': [str(1*1024), str(64)],
            'medium': [str(1*1024), str(512)],
            'large': [str(2*1024), str(1024)],
        },
        'omp_hash_join': {
            # total elements, bucket size, total keys, 1 / hit ratio, check, warm
            'test': [str(x) for x in [512, 8, 128, 8, 1, 1]],
            'small': [str(x) for x in [1 * 1024 * 1024 / 16, 8, 1 * 1024 * 1024 / 8, 8, 1, 1]],
            'medium': [str(x) for x in [2 * 1024 * 1024 / 16, 8, 2 * 1024 * 1024 / 8, 8, 1, 1]],
            'large': [str(x) for x in [4 * 1024 * 1024 / 16, 8, 4 * 1024 * 1024 / 8, 8, 0, 1]],
            'mix': [str(x) for x in [16 * 1024 * 1024 / 16, 8, 128 * 1024 * 1024 / 8, 8, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 16, 8, 64 * 1024 * 1024 / 8, 8, 0, 0]],
        },
        'omp_binary_tree': {
            # total elements, total keys, 1 / hit ratio, check
            'test': [str(x) for x in [512, 128, 8, 1]],
            'small': [str(x) for x in [4 * 1024 * 1024 / 32, 1 * 1024 / 8, 8, 1]],
            'medium': [str(x) for x in [2 * 1024 * 1024 / 32, 2 * 1024 * 1024 / 8, 8, 1]],
            'large': [str(x) for x in [4 * 1024 * 1024 / 32, 4 * 1024 * 1024 / 8, 8, 0]],
        },
        'omp_array_sum_avx': {
            # total elements (float), check, warm
            'medium': [str(x) for x in [1 * 1024 * 1024 / 4, 1, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024 / 4, 0, 0]],
            'large': [str(x) for x in [16 * 1024 * 1024 / 4, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4, 0, 0]],
        },
        'omp_dot_prod_avx': {
            # total elements (float), check, warm
            'medium': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 0]],
            'large': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4 / 2, 0, 0]],
        },
        'omp_vec_add_avx': {
            # total elements (float), check, warm
            'medium': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 0]],
            'large': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4 / 2, 0, 0]],
        },
        # 'omp_histogram_avx': {
        #     'medium': [str(x) for x in [1 * 1024 * 1024 / 4]],
        #     'large': [str(x) for x in [48 * 1024 * 1024 / 4]],
        # }
    }

    def __init__(self, benchmark_args, src_path):
        self.cwd = os.getcwd()
        self.src_path = src_path
        self.suite_path = src_path
        while os.path.basename(self.suite_path) != 'GemForgeMicroSuite':
            self.suite_path = os.path.dirname(self.suite_path)
        self.benchmark_name = os.path.basename(self.src_path)
        self.source = self.benchmark_name + '.c'
        self.graph_utils_source = '../gfm_graph_utils.c'
        self.stream_whitelist_fn = os.path.join(
            self.src_path, 'stream_whitelist.txt')

        self.is_omp = self.benchmark_name.startswith('omp_')
        self.is_avx512 = 'avx' in self.benchmark_name
        self.is_graph = os.path.basename(
            os.path.dirname(self.src_path)) == 'graph'
        self.n_thread = benchmark_args.options.input_threads

        self.is_variant_input = False
        self.variant_input_sizes = None
        for prefix in GemForgeMicroBenchmark.INPUT_SIZE:
            if self.benchmark_name.startswith(prefix):
                self.is_variant_input = True
                self.variant_input_sizes = GemForgeMicroBenchmark.INPUT_SIZE[prefix]

        # Create the result dir out of the source tree.
        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, 'gfm', self.benchmark_name
        )
        Util.mkdir_chain(self.work_path)

        super(GemForgeMicroBenchmark, self).__init__(benchmark_args)

    def get_name(self):
        return 'gfm.{b}'.format(b=self.benchmark_name)

    def get_sim_input_args(self, input_name):
        if self.is_variant_input:
            input_sizes = self.variant_input_sizes
            if input_name not in input_sizes:
                print(f'{self.benchmark_name} Missing Input Size {input_name}')
                assert(False)
            return input_sizes[input_name]
        return list()

    def get_links(self):
        if self.is_omp:
            return [
                '-lomp',
                '-lpthread',
                '-Wl,--no-as-needed',
                '-ldl',
            ]
        return []

    def get_args(self, input_name):
        if self.is_omp:
            args = [str(self.n_thread)]
            if self.is_graph:
                graphs = os.path.join(os.getenv('BENCHMARK_PATH'), 'graphs')
                suffix = 'wbin' if self.benchmark_name.startswith(
                    'omp_sssp_') else 'bin'
                args.append(os.path.join(graphs, '{i}.{s}'.format(
                    i=input_name, s=suffix)))
            args += self.get_sim_input_args(input_name)
            return args
        return None

    def get_extra_compile_flags(self):
        flags = list()
        avx512_workloads = [
            'omp_array_sum_avx',
            'omp_array_sum_avx_int',
            'omp_conv3d2',
            'omp_conv3d2_no_unroll',
            'omp_conv3d2_unroll',
            'omp_conv3d2_unroll_xy',
            'omp_dense_mv_blk',
            'omp_dense_mv',
        ]
        if self.benchmark_name in avx512_workloads or self.is_avx512:
            flags.append('-mavx512f')
        if self.benchmark_name.endswith('histogram_avx'):
            flags.append('-mavx512dq')
            flags.append('-mavx512vl')
        return flags

    def get_sim_input_name(self, sim_input):
        # Only these workloads has sim_input_name.
        sim_name = f'thread{self.n_thread}'
        if self.is_graph or self.is_variant_input:
            sim_name = f'{sim_name}-{sim_input}'
        return sim_name

    OMP_GRAPH_FUNC_SUFFIX = {
        'omp_bfs': [''],
        'omp_bfs_queue': [''],
        'omp_page_rank': ['', '.1'],
        'omp_sssp_bellman': [''],
    }

    def get_trace_func(self):
        if self.is_omp:
            if self.is_graph:
                suffixes = GemForgeMicroBenchmark.OMP_GRAPH_FUNC_SUFFIX[self.benchmark_name]
                return Benchmark.ROI_FUNC_SEPARATOR.join(
                    ['.omp_outlined.' + suffix for suffix in suffixes])
            return '.omp_outlined.'
        else:
            return 'foo'

    def get_lang(self):
        return 'C'

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
            # '-fno-unroll-loops',
            # '-fno-vectorize',
            # '-fno-slp-vectorize',
            # '-mavx512f',
            # '-ffast-math',
            # '-ffp-contract=off',
            '-stream-specialize',
            '-mllvm',
            '-loop-unswitch-threshold=1',
            '-I{GFM_INC}'.format(GFM_INC=self.suite_path),
        ] + self.get_extra_compile_flags()
        no_unroll_workloads = [
            'omp_bfs',
            'omp_page_rank',
            'omp_array_sum_avx',
            'omp_dot_prod_avx',
            'omp_vec_add_avx',
        ]
        for prefix in no_unroll_workloads:
            if self.benchmark_name.startswith(prefix):
                flags.append('-fno-unroll-loops')
                flags.append('-fno-vectorize')
                break

        if self.is_omp:
            flags.append('-fopenmp')
        sources = [self.source]
        if self.is_graph:
            sources.append(self.graph_utils_source)
        bcs = [s[:-2] + '.bc' for s in sources]
        for source, bytecode in zip(sources, bcs):
            compile_cmd = [
                C.CC,
                source,
                '-O3',
                '-c',
                '-DGEM_FORGE',
                '-Rpass-analysis=loop-vectorize',
            ] + flags + [
                '-emit-llvm',
                '-std=c11',
                '-gline-tables-only',
                '-I{INCLUDE}'.format(INCLUDE=C.GEM5_INCLUDE_DIR),
                '-mllvm',
                '-enable-load-pre=true',
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
        """
        Adhoc stream whitelist file as additional option.
        """
        ret = list()
        if os.path.isfile(self.stream_whitelist_fn):
            ret.append(
                '-stream-whitelist-file={whitelist}'.format(
                    whitelist=self.stream_whitelist_fn)
            )
        return ret

    def trace(self):
        print('what?')
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

    def build_validation(self, transform_config, trace, output_tdg):
        # Build the validation binary.
        output_dir = os.path.dirname(output_tdg)
        binary = os.path.join(output_dir, self.get_valid_bin())
        build_cmd = [
            C.CC,
            '-static',
            '-O3',
            self.get_raw_bc(),
            # Link with gem5.
            '-I{gem5_include}'.format(gem5_include=C.GEM5_INCLUDE_DIR),
            C.GEM5_M5OPS_X86,
            '-lm',
            '-o',
            binary
        ]
        Util.call_helper(build_cmd)
        asm = os.path.join(output_dir, self.get_name() + '.asm')
        with open(asm, 'w') as f:
            disasm_cmd = [
                'objdump',
                '-d',
                binary
            ]
            Util.call_helper(disasm_cmd, stdout=f)

    def get_additional_gem5_simulate_command(self, transform_config, simulation_config, input_name):
        """
        Some benchmarks takes too long to finish, so we use work item
        to ensure that we simualte for the same amount of work.
        """
        flags = list()
        work_items = -1
        if self.benchmark_name == 'omp_page_rank':
            # One iteration, two kernels.
            work_items = 2
        if self.benchmark_name == 'omp_bfs':
            # Try to finish them?
            work_items = -1
        if work_items != -1:
            flags.append(
                '--work-end-exit-count={v}'.format(v=work_items),
            )
        if self.is_variant_input:
            flags.append(
                '--cpu-yield-lat=4000ns',
            )
        if self.benchmark_name == 'omp_indirect_sum':
            # Disable deadlock check for this workload as we are offloading long indirect access.
            flags.append(
                '--gem-forge-cpu-deadlock-interval=0ns',
            )
        if self.benchmark_name.startswith('omp_dot_prod_avx'):
            flags.append(
                '--gem-forge-cpu-deadlock-interval=0ns',
            )
        return flags

    def get_gem5_mem_size(self):
        if not self.is_omp:
            return '128MB'
        return None


class GemForgeMicroSuite:

    def searchBenchmarks(self, benchmark_args, folder):
        # Every folder in the suite is a benchmark.
        items = os.listdir(folder)
        items.sort()
        for item in items:
            if item[0] == '.':
                # Ignore special folders.
                continue
            abs_path = os.path.join(folder, item)
            abs_source_path = os.path.join(abs_path, item + '.c')
            if os.path.isdir(abs_path):
                if os.path.isfile(abs_source_path):
                    benchmark_name = 'gfm.{b}'.format(b=item)
                    if benchmark_args.options.benchmark:
                        if benchmark_name not in benchmark_args.options.benchmark:
                            # Ignore benchmark not required.
                            continue
                    self.benchmarks.append(
                        GemForgeMicroBenchmark(benchmark_args, abs_path))
                else:
                    # Recursive search for deeper benchmarks:
                    self.searchBenchmarks(benchmark_args, abs_path)

    def __init__(self, benchmark_args):
        suite_folder = os.path.join(
            C.GEM_FORGE_BENCHMARK_PATH, 'GemForgeMicroSuite')
        self.benchmarks = list()
        self.searchBenchmarks(benchmark_args, suite_folder)

    def get_benchmarks(self):
        return self.benchmarks
