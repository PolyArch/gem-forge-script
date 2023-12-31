import Util
import Constants as C
from BenchmarkDrivers.Benchmark import Benchmark

from Utils import TraceFlagEnum

import os


class CortexBenchmark(Benchmark):

    O2 = ['O2']
    O2_NO_VECTORIZE = ['O3', 'fno-vectorize',
                       'fno-slp-vectorize', 'fno-unroll-loops']
    O3 = ['O3']

    FLAGS_STREAM = {
        # Advanced stream experiments.
        # RBM has vectorized loop with extra iterations.
        # So far we can not handle it.
        'rbm': O3,
        'sphinx': O3,
        'srr': O3,
        'lda': O3,
        'svd3': O3,
        'pca': O3,
        'motion-estimation': O3,
        'liblinear': O3,
    }

    FLAGS_FRACTAL = {
        # Fractal experiments.
        'rbm': O2_NO_VECTORIZE,
        'sphinx': O2_NO_VECTORIZE,
        'srr': O2_NO_VECTORIZE,
        'lda': O2_NO_VECTORIZE,
        'svd3': O2_NO_VECTORIZE,
        'pca': O2_NO_VECTORIZE,
        'motion-estimation': O2_NO_VECTORIZE,
        'liblinear': O2_NO_VECTORIZE,
    }

    DEFINES = {
        'rbm': {
            'small': {
                'USERS': 10,
                'TEST_USERS': 10,
                'MOVIES': 10,
                'LOOPS': 20,
            },
            'medium': {
                'USERS': 100,
                'TEST_USERS': 100,
                'MOVIES': 100,
                'LOOPS': 20,
            },
            'large': {
                'USERS': 100,
                'TEST_USERS': 100,
                'MOVIES': 100,
                'LOOPS': 200,
            },
        },
        'sphinx': {
            'small': {},
            'medium': {},
            'large': {},
        },
        'srr': {
            'small': {
                'SYNTHETIC1': None,
            },
            'medium': {
                'ALPACA': None,
            },
            'large': {
                'BOOKCASE': None,
            },
        },
        'lda': {
            'small': {},
            'medium': {},
            'large': {},
        },
        'svd3': {
            'small': {},
            'medium': {},
            'large': {},
        },
        'pca': {
            'small': {},
            'medium': {},
            'large': {},
        },
        'motion-estimation': {
            'small': {
                'SYNTHETIC1': None,
            },
            'medium': {
                'ALPACA': None,
            },
            'large': {
                'BOOKCASE': None,
            },
        },
        'liblinear': {
            'small': {},
            'medium': {},
            'large': {},
        },
    }

    TRACE_FUNC = {
        'lda': ['compute_likelihood', 'lda_inference'],
        'liblinear': ['solve_l2r_l1l2_svc'],
        'motion-estimation': ['Motion_Est', 'FullSearch'],
        'pca': ['corcol'],
        'rbm': ['train'],
        'sphinx': ['lm3g_tg_score.1975', 'hmm_vit_eval', 'ngram_search_hyp'],
        'srr': ['get_b', 'solve_pixel', 'get_g'],
        'svd3': ['svd'],
    }

    ARGS = {
        'rbm': {
            'small': [],
            'medium': [],
            'large': [],
        },
        'sphinx': {
            'small': ['small/audio.raw', 'language_model/turtle/'],
            'medium': ['medium/audio.raw', 'language_model/HUB4/'],
            'large': ['large/audio.raw', 'language_model/HUB4/'],
        },
        'srr': {
            'small': [],
            'medium': [],
            'large': [],
        },
        'lda': {
            'small': ['est', '.1', '3', 'settings.txt', 'small/small_data.dat', 'random', 'small/result'],
            'medium': ['est', '.1', '3', 'settings.txt', 'medium/medium_data.dat', 'random', 'medium/result'],
            'large': ['est', '.1', '3', 'settings.txt', 'large/large_data.dat', 'random', 'large/result'],
        },
        'svd3': {
            'small': ['small.txt'],
            'medium': ['med.txt'],
            'large': ['large.txt'],
        },
        'pca': {
            'small': ['small.data', '1593', '256', 'R'],
            'medium': ['medium.data', '722', '800', 'R'],
            'large': ['large.data', '5000', '1059', 'R'],
        },
        'motion-estimation': {
            'small': [],
            'medium': [],
            'large': [],
        },
        'liblinear': {
            'small': ['data/100M/crime_scale'],
            'medium': ['data/10B/epsilon'],
            'large': ['data/100B/kdda'],
        },
    }

    TRACE_IDS = {
        # 'rbm': 0],
        # 'sphinx': [8],
        # 'srr': [1],
        # 'lda': [1],
        # 'svd3': [0,1,2,4,5,6,7,8,9],
        # 'pca': [1],
        # 'motion-estimation': [0,1,3,8],
        # 'liblinear': [0],
        'rbm': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'sphinx': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'srr': [0, 1, 2, 3, 4, 5, 6, 8, 9],
        'lda': [0],
        'svd3': [0, 1, 2, 4, 5, 6, 7, 8, 9],
        'pca': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'motion-estimation': [0, 1, 3, 8],
        'liblinear': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    }

    LEGAL_INPUT_SIZE = ('small', 'medium', 'large')

    def __init__(self, benchmark_args,
                 folder, benchmark_name, suite='cortex'):
        self.benchmark_name = benchmark_name

        self.input_name = 'large'
        if benchmark_args.options.input_name:
            self.input_name = benchmark_args.options.input_name
        assert(self.input_name in CortexBenchmark.LEGAL_INPUT_SIZE)
        self.sim_input_name = 'large'
        if benchmark_args.options.sim_input_name:
            self.sim_input_name = benchmark_args.options.sim_input_name
        assert(self.sim_input_name in CortexBenchmark.LEGAL_INPUT_SIZE)

        self.suite = suite
        self.top_folder = folder

        self.src_dir = os.path.join(self.top_folder, benchmark_name)

        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, self.suite, self.benchmark_name)
        Util.mkdir_chain(self.work_path)

        # Create a symbolic link for everything in the source dir.
        for f in os.listdir(self.src_dir):
            print(os.path.join(self.src_dir, f))
            source = os.path.join(self.src_dir, f)
            dest = os.path.join(self.work_path, f)
            Util.create_symbolic_link(source, dest)

        self.cwd = os.getcwd()
        if C.EXPERIMENTS == 'stream':
            self.flags = CortexBenchmark.FLAGS_STREAM[self.benchmark_name]
        elif C.EXPERIMENTS == 'fractal':
            self.flags = CortexBenchmark.FLAGS_FRACTAL[self.benchmark_name]
        self.flags.append('gline-tables-only')

        self.defines = CortexBenchmark.DEFINES[self.benchmark_name][self.input_name]

        self.includes = ['includes']
        self.trace_functions = Benchmark.ROI_FUNC_SEPARATOR.join(
            CortexBenchmark.TRACE_FUNC[self.benchmark_name])

        self.trace_ids = CortexBenchmark.TRACE_IDS[self.benchmark_name]
        self.start_inst = 1
        self.max_inst = 1e7
        self.skip_inst = 1e8
        self.end_inst = 11e8

        super(CortexBenchmark, self).__init__(benchmark_args)

    def get_name(self):
        return '{suite}.{benchmark_name}'.format(
            suite=self.suite,
            benchmark_name=self.benchmark_name,
        )

    def get_input_name(self):
        return self.input_name

    def get_sim_input_name(self):
        return self.sim_input_name

    def get_profile_roi(self):
        if self.input_name == 'small':
            return TraceFlagEnum.GemForgeTraceROI.SpecifiedFunction.value
        return TraceFlagEnum.GemForgeTraceROI.All.value

    def get_links(self):
        return ['-lm']

    def get_args(self):
        return CortexBenchmark.ARGS[self.benchmark_name][self.input_name]

    def get_sim_args(self):
        return CortexBenchmark.ARGS[self.benchmark_name][self.sim_input_name]

    def get_trace_func(self):
        return self.trace_functions

    def get_lang(self):
        return 'C'

    def get_exe_path(self):
        return self.work_path

    def get_run_path(self):
        return self.work_path

    def find_all_sources(self, folder):
        sources = list()
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith('.c'):
                    # Special case for one lm3g_templates.c for sphinx,
                    # which should not be compiled.
                    if f == 'lm3g_templates.c' and self.benchmark_name == 'sphinx':
                        continue
                    sources.append(os.path.join(root, f))
        return sources

    def compile(self, source, flags, defines, includes):
        compiler = C.CC if source.endswith('.c') else C.CXX
        bc = source + '.bc'
        self.debug('Compiling {source} to {bc}.'.format(source=source, bc=bc))
        compile_cmd = [
            compiler,
            source,
            '-c',
            '-emit-llvm',
            '-o',
            bc,
        ]
        for flag in flags:
            compile_cmd.append('-{flag}'.format(flag=flag))
        for define in defines:
            if defines[define] is not None:
                compile_cmd.append(
                    '-D{DEFINE}={VALUE}'.format(DEFINE=define, VALUE=defines[define]))
            else:
                compile_cmd.append('-D{DEFINE}'.format(DEFINE=define))
        for include in includes:
            compile_cmd.append('-I{INCLUDE}'.format(INCLUDE=include))
        Util.call_helper(compile_cmd)
        Util.call_helper([C.OPT, '-instnamer', bc, '-o', bc])
        Util.call_helper([C.LLVM_DIS, bc])
        return bc

    def build_raw_bc(self):
        self.debug('Build raw bitcode.')
        os.chdir(self.work_path)

        sources = self.find_all_sources(self.src_dir)
        bcs = [self.compile(s, self.flags, self.defines,
                            self.includes) for s in sources]

        raw_bc = self.get_raw_bc()
        link_cmd = [C.LLVM_LINK] + bcs + ['-o', raw_bc]
        self.debug('Linking to raw bitcode {raw_bc}'.format(raw_bc=raw_bc))
        Util.call_helper(link_cmd)

        self.post_build_raw_bc(raw_bc)

        os.chdir(self.cwd)

    def trace(self):
        os.chdir(self.work_path)
        self.build_trace(
            trace_reachable_only=False,
        )

        if self.input_name != 'large':
            # For non fullhd input we trace only the traced function.
            os.putenv('LLVM_TDG_TRACE_ROI', str(
                TraceFlagEnum.GemForgeTraceROI.SpecifiedFunction.value
            ))
            os.putenv('LLVM_TDG_TRACE_MODE', str(
                TraceFlagEnum.GemForgeTraceMode.TraceAll.value
            ))
        else:
            # Otherwise we trace the simpoint region.
            os.putenv('LLVM_TDG_TRACE_ROI', str(
                TraceFlagEnum.GemForgeTraceROI.All.value
            ))
            os.putenv('LLVM_TDG_TRACE_MODE', str(
                TraceFlagEnum.GemForgeTraceMode.TraceSpecifiedInterval.value
            ))
            os.putenv('LLVM_TDG_INTERVALS_FILE', self.get_simpoint_abs())

        self.run_trace()
        os.chdir(self.cwd)


class CortexSuite:
    def __init__(self, benchmark_args):
        folder = os.getenv('CORTEX_SUITE_PATH')
        assert(folder is not None)
        self.benchmarks = list()
        for benchmark_name in CortexBenchmark.FLAGS_STREAM:
            if benchmark_args.options.benchmark:
                full_name = 'cortex.{b}'.format(b=benchmark_name)
                if full_name not in benchmark_args.options.benchmark:
                    # Ignore benchmark not required.
                    continue
            benchmark = CortexBenchmark(
                benchmark_args, folder, benchmark_name)
            self.benchmarks.append(benchmark)

    def get_benchmarks(self):
        return self.benchmarks
