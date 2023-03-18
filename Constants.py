
import os

# Where is GemForge
GEM_FORGE_TRANSFORM_PATH = os.getenv('GEM_FORGE_TRANSFORM_PATH')
assert(GEM_FORGE_TRANSFORM_PATH is not None)
GEM_FORGE_TRANSFORM_BUILD_PATH = os.path.join(GEM_FORGE_TRANSFORM_PATH, 'build')
GEM_FORGE_DRIVER_PATH = os.path.join(GEM_FORGE_TRANSFORM_PATH, '../driver')
GEM_FORGE_BENCHMARK_PATH = os.path.join(GEM_FORGE_TRANSFORM_PATH, 'benchmark')

AFFINITY_ALLOC_INC_PATH = os.path.join(GEM_FORGE_TRANSFORM_PATH, 'src/affinity_alloc')
AFFINITY_ALLOC_LIB_PATH = os.path.join(GEM_FORGE_TRANSFORM_BUILD_PATH, 'src/affinity_alloc')

# Where to store the llvm_bc and traces.
EXPERIMENTS = 'stream'
# EXPERIMENTS = 'fractal'
GEM_FORGE_RESULT_PATH = os.path.join(
    os.getenv('GEM_FORGE_RESULT_PATH'), EXPERIMENTS)

LLVM_TDG_REPLAY_C = os.path.join(GEM_FORGE_DRIVER_PATH, 'replay.c')

"""
Normal llvm install path.
"""
LLVM_PATH = os.getenv('LLVM_RELEASE_INSTALL_PATH')
assert(LLVM_PATH is not None)
LLVM_BIN_PATH = os.path.join(LLVM_PATH, 'bin')
LLVM_LIB_PATH = os.path.join(LLVM_PATH, 'lib')
LLVM_DEBUG_PATH = os.getenv('LLVM_DEBUG_INSTALL_PATH')
LLVM_DEBUG_BIN_PATH = os.path.join(LLVM_DEBUG_PATH, 'bin')

PERF_BIN = os.getenv('PERF_BIN')
if PERF_BIN is None:
    PERF_BIN = 'perf'

"""
GEM5_PATH
"""
GEM5_DIR = os.getenv('GEM_FORGE_GEM5_PATH')
GEM5_INCLUDE_DIR = os.path.join(GEM5_DIR, 'include')
GEM5_X86 = os.path.join(GEM5_DIR, 'build/X86/gem5.opt')
GEM5_RISCV = os.path.join(GEM5_DIR, 'build/RISCV/gem5.opt')
GEM5_LLVM_TRACE_SE_CONFIG = os.path.join(
    GEM5_DIR, 'configs/example/gem_forge/run.py')
GEM5_SE_CONFIG = os.path.join(
    GEM5_DIR, 'configs/example/se.py')
GEM5_M5OPS_X86 = os.path.join(GEM5_DIR, 'util', 'm5', 'm5op_x86.S')
GEM5_M5OPS_RISCV = os.path.join(GEM5_DIR, 'util', 'm5', 'm5op_riscv.S')
GEM5_M5OPS_EMPTY = os.path.join(GEM5_DIR, 'util', 'm5', 'm5op_empty.cpp')
DRAMSIM3_DIR = os.path.join(GEM5_DIR, 'ext/dramsim3/DRAMsim3')

M5_THREADS_LIB = os.getenv('M5_THREADS_LIB')

"""
Gem5 parameters.
"""
# CPU_TYPE = 'DerivO3CPU'
# CPU_TYPE = 'TimingSimpleCPU'
CPU_TYPE = 'MinorCPU'
STORE_QUEUE_SIZE = 32
GEM5_USE_MCPAT = 0

OPT = os.path.join(LLVM_DEBUG_BIN_PATH, 'opt')
CC = os.path.join(LLVM_BIN_PATH, 'clang')
CXX = os.path.join(LLVM_BIN_PATH, 'clang++')
LLVM_LINK = os.path.join(LLVM_BIN_PATH, 'llvm-link')
LLVM_DIS = os.path.join(LLVM_BIN_PATH, 'llvm-dis')
LLVM_OBJDUMP = os.path.join(LLVM_BIN_PATH, 'llvm-objdump')

# We may need DEBUG compiler.
CC_DEBUG = os.path.join(LLVM_DEBUG_BIN_PATH, 'clang')
CXX_DEBUG = os.path.join(LLVM_DEBUG_BIN_PATH, 'clang++')
LLVM_OBJDUMP_DEBUG = os.path.join(LLVM_DEBUG_BIN_PATH, 'llvm-objdump')

# Some one installed a wrong version of protobuf on my computer.
# PROTOBUF_LIB = os.getenv('LIBPROTOBUF_STATIC_LIB')
# if PROTOBUF_LIB is None:
#     print('Missing env var LIBPROTOBUF_STATIC_LIB')
#     assert(False)
PROTOBUF_LIB = '-lprotobuf'
LIBUNWIND_LIB = '-lunwind'

# Additional path to look for libstdc++.
LIBSTDCXX_SYSTEM = os.getenv('LIBSTDCXX_SYSTEM')
LIBSTDCXX_INCLUDE = os.getenv('LIBSTDCXX_INCLUDE')
LIBSTDCXX_LIBRARY = os.getenv('LIBSTDCXX_LIBRARY')

ISA = 'x86'
# ISA = 'riscv'


def get_native_cxx_compiler(CXX):
    if LIBSTDCXX_SYSTEM is None:
        return [CXX]
    return [
        CXX,
        '-isystem={S}'.format(S=LIBSTDCXX_SYSTEM),
        '-I{S}'.format(S=LIBSTDCXX_INCLUDE),
        '-L{S}'.format(S=LIBSTDCXX_LIBRARY),
    ]


def get_sim_compiler(compiler):
    if ISA == 'x86':
        return [compiler]
    if ISA == 'riscv':
        return [
            compiler,
            '--target=riscv64-unknown-linux-gnu',
            '-march=rv64g',
            '-mabi=lp64d',
        ]


def get_sim_linker():
    """
    Get the linker to generate binary for gem5 simulation.
    """
    if ISA == 'x86':
        # Simply use native clang++ to link.
        return get_native_cxx_compiler(CXX)
    if ISA == 'riscv':
        # Clang support for linking RISCV is not working.
        # Use the cross compiler of g++.
        RISCV_GNU_INSTALL_PATH = os.getenv('RISCV_GNU_INSTALL_PATH')
        assert(RISCV_GNU_INSTALL_PATH is not None)
        return [
            os.path.join(RISCV_GNU_INSTALL_PATH,
                         'bin/riscv64-unknown-linux-gnu-g++'),
            '-march=rv64g',
            '-mabi=lp64d',
        ]


def get_gem5_m5ops():
    if ISA == 'x86':
        return GEM5_M5OPS_X86
    if ISA == 'riscv':
        return GEM5_M5OPS_RISCV


def get_gem5():
    if ISA == 'x86':
        return GEM5_X86
    if ISA == 'riscv':
        return GEM5_RISCV
