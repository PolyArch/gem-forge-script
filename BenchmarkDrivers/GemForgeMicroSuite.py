
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
            # nodes per list, num of lists, check, warm
            'test': [str(64), str(64)],
            'small': [str(1*128), str(64)],
            'medium': [str(1*256), str(512)],
            'large': [str(x) for x in [32 * 1024 / 64, 1024, 0, 1]],
            'large-cold': [str(x) for x in [32 * 1024 / 64, 1024, 0, 0]],
            'mix': [str(x) for x in [512 * 1024 / 64, 1024, 0, 0]],
        },
        'omp_link_list_search_bulk64': {
            # nodes per list, num of lists, check, warm
            'large': [str(x) for x in [32 * 1024 / 64, 1024, 0, 1]],
            'mix': [str(x) for x in [512 * 1024 / 64, 1024, 0, 0]],
        },
        'omp_link_list_search_bulk2k': {
            # nodes per list, num of lists, check, warm
            'large': [str(x) for x in [32 * 1024 / 64, 1024, 0, 1]],
            'mix': [str(x) for x in [512 * 1024 / 64, 1024, 0, 0]],
        },
        'omp_hash_join': {
            # total elements, bucket size, total keys, 1 / hit ratio, check, warm
            'test': [str(x) for x in [512, 8, 128, 8, 1, 1]],
            'small': [str(x) for x in [1 * 1024 * 1024 / 16, 8, 1 * 1024 * 1024 / 8, 8, 1, 1]],
            'medium': [str(x) for x in [2 * 1024 * 1024 / 16, 8, 2 * 1024 * 1024 / 8, 8, 1, 1]],
            'large': [str(x) for x in [4 * 1024 * 1024 / 16, 8, 4 * 1024 * 1024 / 8, 8, 0, 1]],
            'mix': [str(x) for x in [512 * 1024 * 1024 / 16, 8, 4 * 1024 * 1024 / 8, 8, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 16, 8, 64 * 1024 * 1024 / 8, 8, 0, 0]],
        },
        'omp_binary_tree': {
            # total elements, total keys, 1 / hit ratio, check, warm
            'test': [str(x) for x in [512, 128, 8, 1, 1]],
            'small': [str(x) for x in [4 * 1024 * 1024 // 64, 1 * 1024 // 8, 8, 1, 1]],
            'medium': [str(x) for x in [2 * 1024 * 1024 // 64, 2 * 1024 * 1024 // 8, 8, 1, 1]],
            'large': [str(x) for x in [8 * 1024 * 1024 // 64, 4 * 1024 * 1024 // 8, 8, 0, 1]],
            'large-cold': [str(x) for x in [8 * 1024 * 1024 // 64, 4 * 1024 * 1024 // 8, 8, 0, 0]],
            'mix': [str(x) for x in [512 * 1024 * 1024 // 64, 4 * 1024 * 1024 // 8, 8, 0, 1]],
        },
        'array_sum': {
            # total elements (float), check, warm
            'teeny': [str(x) for x in [16 * 1024, 0, 1]],
            'teeny-cold': [str(x) for x in [16 * 1024, 0, 0]],
            'tiny': [str(x) for x in [64 * 1024, 0, 1]],
            'tiny-cold': [str(x) for x in [64 * 1024, 0, 0]],
            'small': [str(x) for x in [256 * 1024, 0, 1]],
            'small-cold': [str(x) for x in [256 * 1024, 0, 0]],
            'medium': [str(x) for x in [1 * 1024 * 1024, 0, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024, 0, 0]],
            'large': [str(x) for x in [4 * 1024 * 1024, 0, 1]],
            'large-cold': [str(x) for x in [4 * 1024 * 1024, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4, 0, 0]],
        },
        'vec_add': {
            # total elements (float), check, warm
            'teeny': [str(x) for x in [16 * 1024, 0, 1]],
            'teeny-cold': [str(x) for x in [16 * 1024, 0, 0]],
            'tiny': [str(x) for x in [64 * 1024, 0, 1]],
            'tiny-cold': [str(x) for x in [64 * 1024, 0, 0]],
            'small': [str(x) for x in [256 * 1024, 0, 1]],
            'small-cold': [str(x) for x in [256 * 1024, 0, 0]],
            'medium': [str(x) for x in [1 * 1024 * 1024, 0, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024, 0, 0]],
            'large': [str(x) for x in [4 * 1024 * 1024, 0, 1]],
            'large-cold': [str(x) for x in [4 * 1024 * 1024, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4 / 2, 0, 0]],
        },
        'omp_dot_prod_avx': {
            # total elements (float), check, warm
            'medium': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 1]],
            'medium-cold': [str(x) for x in [1 * 1024 * 1024 / 4 / 2, 1, 0]],
            'large': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 0]],
            'mem': [str(x) for x in [64 * 1024 * 1024 / 4 / 2, 0, 0]],
        },
        'stencil1d': {
            # total elements (float, 3 array), rounds, check, warm
            'tiny': [str(x) for x in [256 * 1024 / 4, 10, 0, 1]],
            'tiny-cold': [str(x) for x in [256 * 1024 / 4, 10, 0, 0]],
            'small': [str(x) for x in [1 * 1024 * 1024 / 4, 10, 0, 1]],
            'small-cold': [str(x) for x in [1 * 1024 * 1024 / 4, 10, 0, 0]],
            'medium': [str(x) for x in [4 * 1024 * 1024 / 4, 1, 0, 1]],
            'medium-cold': [str(x) for x in [4 * 1024 * 1024 / 4, 1, 0, 0]],
            'large': [str(x) for x in [16 * 1024 * 1024 / 4, 1, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4, 1, 0, 0]],
            'large2x': [str(x) for x in [32 * 1024 * 1024 / 4, 1, 0, 1]],
            'large2x-cold': [str(x) for x in [32 * 1024 * 1024 / 4, 1, 0, 0]],
        },
        'stencil2d': {
            # M, N, (float, 3 array), rounds, check, warm
            'tiny': [str(x) for x in [256, 256, 10, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 10, 0, 0]],
            'small': [str(x) for x in [512, 512, 10, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 10, 0, 0]],
            'medium': [str(x) for x in [1 * 1024, 1 * 1024, 1, 0, 1]],
            'medium-cold': [str(x) for x in [1 * 1024, 1 * 1024, 1, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 1, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 1, 0, 0]],
            'large2x': [str(x) for x in [4 * 1024, 2 * 1024, 1, 0, 1]],
            'large2x-cold': [str(x) for x in [4 * 1024, 2 * 1024, 1, 0, 0]],
            'duality': [str(x) for x in [512, 512, 2, 0, 1]],
            'duality-cold': [str(x) for x in [512, 512, 2, 0, 0]],
        },
        'stencil3d': {
            # M, N, L, (float, 3 array), rounds, check, warm
            'tiny': [str(x) for x in [64, 64, 8, 10, 0, 1]],
            'tiny-cold': [str(x) for x in [64, 64, 8, 10, 0, 0]],
            'small': [str(x) for x in [128, 128, 8, 10, 0, 1]],
            'small-cold': [str(x) for x in [128, 128, 8, 10, 0, 0]],
            'medium': [str(x) for x in [256, 256, 16, 1, 0, 1]],
            'medium-cold': [str(x) for x in [256, 256, 16, 1, 0, 0]],
            'large': [str(x) for x in [512, 512, 16, 1, 0, 1]],
            'large-cold': [str(x) for x in [512, 512, 16, 1, 0, 0]],
            'large2x': [str(x) for x in [512, 512, 32, 1, 0, 1]],
            'large2x-cold': [str(x) for x in [512, 512, 32, 1, 0, 0]],
            'duality': [str(x) for x in [512, 512, 8, 100, 0, 1]],
            'duality-cold': [str(x) for x in [512, 512, 8, 100, 0, 0]],
        },
        'gaussian_elim': {
            # M, N, P, (float, 1 array), check, warm
            'tiny': [str(x) for x in [256, 256, 64, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 64, 0, 0]],
            'small': [str(x) for x in [512, 512, 64, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 64, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 64, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 64, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 64, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 64, 0, 0]],
            'large2x': [str(x) for x in [4 * 1024, 2 * 1024, 64, 0, 1]],
            'large2x-cold': [str(x) for x in [4 * 1024, 2 * 1024, 64, 0, 0]],
            'duality': [str(x) for x in [256, 256, 256, 0, 1]],
            'duality-cold': [str(x) for x in [256, 256, 256, 0, 0]],
        },
        'dwt2d53': {
            # M, N, level, (float, 2 arrays), check, warm
            'tiny': [str(x) for x in [256, 256, 1, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 1, 0, 0]],
            'small': [str(x) for x in [512, 512, 1, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 1, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 1, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 1, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 1, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 1, 0, 0]],
            'large2x': [str(x) for x in [4 * 1024, 2 * 1024, 1, 0, 1]],
            'large2x-cold': [str(x) for x in [4 * 1024, 2 * 1024, 1, 0, 0]],
            'duality': [str(x) for x in [1024, 1024, 3, 0, 1]],
            'duality-cold': [str(x) for x in [1024, 1024, 3, 0, 0]],
        },
        'mm_outer': {
            # L, M, N, (float, 3 array), check, warm
            'tiny': [str(x) for x in [256, 256, 256, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 256, 0, 0]],
            'small': [str(x) for x in [512, 512, 512, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 512, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 1024, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 1024, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 0, 0]],
            'large2x': [str(x) for x in [4 * 1024, 2 * 1024, 2 * 1024, 0, 1]],
            'large2x-cold': [str(x) for x in [4 * 1024, 2 * 1024, 2 * 1024, 0, 0]],
            'largeM': [str(x) for x in [32 * 1024, 128, 128, 0, 1]],
            'largeM-cold': [str(x) for x in [32 * 1024, 128, 128, 0, 0]],
            'largeN': [str(x) for x in [128, 128, 32 * 1024, 0, 1]],
            'largeN-cold': [str(x) for x in [128, 128, 32 * 1024, 0, 0]],
        },
        'mm_inner': {
            # L, M, N, P, (float, 4 array), check, warm
            'tiny': [str(x) for x in [256, 256, 256, 64, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 256, 64, 0, 0]],
            'small': [str(x) for x in [512, 512, 512, 64, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 512, 64, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 1024, 64, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 1024, 64, 0, 0]],
            'strnd': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 2, 0, 1]],
            'strnd-cold': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 2, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 64, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 64, 0, 0]],
            'large2x': [str(x) for x in [2 * 1024, 4 * 1024, 2 * 1024, 64, 0, 1]],
            'large2x-cold': [str(x) for x in [2 * 1024, 4 * 1024, 2 * 1024, 64, 0, 0]],
        },
        'mm_lmn': {
            # L, M, N, P, (float, 4 array), check, warm
            'tiny': [str(x) for x in [256, 256, 256, 64, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 256, 64, 0, 0]],
            'small': [str(x) for x in [512, 512, 512, 64, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 512, 64, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 1024, 64, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 1024, 64, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 64, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 2 * 1024, 64, 0, 0]],
            'large2x': [str(x) for x in [2 * 1024, 4 * 1024, 2 * 1024, 64, 0, 1]],
            'large2x-cold': [str(x) for x in [2 * 1024, 4 * 1024, 2 * 1024, 64, 0, 0]],
        },
        'conv2d': {
            # M, N, (float, 2 array), check, warm
            'tiny': [str(x) for x in [256, 256, 0, 1]],
            'tiny-cold': [str(x) for x in [256, 256, 0, 0]],
            'small': [str(x) for x in [512, 512, 0, 1]],
            'small-cold': [str(x) for x in [512, 512, 0, 0]],
            'medium': [str(x) for x in [1024, 1024, 0, 1]],
            'medium-cold': [str(x) for x in [1024, 1024, 0, 0]],
            'large': [str(x) for x in [2 * 1024, 2 * 1024, 0, 1]],
            'large-cold': [str(x) for x in [2 * 1024, 2 * 1024, 0, 0]],
            'large2x': [str(x) for x in [4 * 1024, 2 * 1024, 0, 1]],
            'large2x-cold': [str(x) for x in [4 * 1024, 2 * 1024, 0, 0]],
        },
        'conv3d_xyz_ioyx_outer': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'tiny': [str(x) for x in [64, 64, 16, 1, 3, 3, 0, 1]],
            'small': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 0]],
            'medium': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 1]],
            'medium-cold': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 0]],
            'large2x': [str(x) for x in [512, 256, 64, 64, 3, 3, 0, 1]],
            'large2x-cold': [str(x) for x in [512, 256, 64, 64, 3, 3, 0, 0]],
        },
        'conv3d_zxy_oyxi_outer_tile': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'tiny': [str(x) for x in [64, 64, 16, 1, 3, 3, 0, 1]],
            'small': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 0]],
            'medium': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 1]],
            'medium-cold': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 16, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 16, 3, 3, 0, 0]],
        },
        'conv3d_zxy_obybxyxi_outer': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'small': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 0]],
        },
        'conv3d_zxy_byboxyxi_outer': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'small': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 0]],
        },
        'conv3d_zxy_fbybx_oxyxi_outer': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'small': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [64, 64, 64, 64, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 0]],
        },
        'conv3d_zxy_inner': {
            # Nx, Ny, Ni, Nn, Kx, Ky, (float, 3 array), check, warm
            'tiny': [str(x) for x in [64, 64, 16, 1, 3, 3, 0, 1]],
            'small': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 1]],
            'small-cold': [str(x) for x in [128, 128, 16, 16, 3, 3, 0, 0]],
            'medium': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 1]],
            'medium-cold': [str(x) for x in [256, 256, 32, 32, 3, 3, 0, 0]],
            'large': [str(x) for x in [256, 256, 64, 64, 3, 3, 0, 1]],
            'large-cold': [str(x) for x in [256, 256, 64, 16, 3, 3, 0, 0]],
        },
        'linear_reuse_avx': {
            # total elements (float), check, warm
            'large': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 1]],
            'large-cold': [str(x) for x in [16 * 1024 * 1024 / 4 / 2, 0, 0]],
        },
        'kmeans': {
            # points (float), dims, centers, check, warm
            'large': [str(x) for x in [32768, 128, 128, 0, 1]],
            'large-cold': [str(x) for x in [32768, 128, 128, 0, 0]],
            'small': [str(x) for x in [2048, 128, 128, 0, 1]],
            'small-cold': [str(x) for x in [2048, 128, 128, 0, 0]],
            'tiny': [str(x) for x in [1024, 128, 128, 0, 1]],
            'tiny-cold': [str(x) for x in [1024, 128, 128, 0, 0]],
            'large2x': [str(x) for x in [64 * 1024, 128, 128, 0, 1]],
            'large2x-cold': [str(x) for x in [64 * 1024, 128, 128, 0, 0]],
        },
        'pointnet': {
            # points (float), dims, features, layers, check, warm
            'small': [str(x) for x in [2048, 128, 4096, 3, 0, 1]],
            'small-cold': [str(x) for x in [2048, 128, 4096, 3, 0]],
            'large': [str(x) for x in [32768, 128, 4096, 3, 0, 1]],
            'large-cold': [str(x) for x in [32768, 128, 4096, 3, 0, 0]],
            'large2x': [str(x) for x in [64 * 1024, 128, 8192, 3, 0, 1]],
            'large2x-cold': [str(x) for x in [64* 1024, 128, 8192, 3, 0, 0]],
        },
        'pntnet2': {
            # isFC, features (float), centroids, neighbors, layers, dims * (layers + 1), radius, check, warm
            'sa1': [str(x) for x in [0, 4096, 512, 32, 3, 64, 64, 64, 128, 0.2, 0, 1]],
            'sa1-cold': [str(x) for x in [0, 4096, 512, 32, 3, 64, 64, 64, 128, 0.2, 0, 0]],
            'sa1l1-cold': [str(x) for x in [0, 4096, 512, 32, 1, 64, 64, 0.2, 0, 0]],
            'sa2': [str(x) for x in [0, 512, 128, 64, 3, 128, 128, 128, 256, 0.4, 0, 1]],
            'sa2-cold': [str(x) for x in [0, 512, 128, 64, 3, 128, 128, 128, 256, 0.4, 0, 0]],
            'sa3': [str(x) for x in [0, 128, 1, 128, 3, 256, 256, 512, 1024, 10000, 0, 1]],
            'sa3-cold': [str(x) for x in [0, 128, 1, 128, 3, 256, 256, 512, 1024, 10000, 0, 0]],
            'sa3l1-cold': [str(x) for x in [0, 128, 1, 128, 1, 256, 256, 10000, 0, 0]],
            'fc-cold': [str(x) for x in [1, 128, 1, 128, 3, 1024, 512, 256, 10, 10000, 0, 0]],
            # 4096x32
            'msg1-sa1-cold': [str(x) for x in [0, 4096, 512, 16, 3, 32, 32, 32, 64, 0.1, 0, 0]],
            # 4096x64
            'msg1-sa2-cold': [str(x) for x in [0, 4096, 512, 32, 3, 64, 64, 64, 128, 0.2, 0, 0]],
            # 4096x64
            'msg1-sa3-cold': [str(x) for x in [0, 4096, 512, 128, 3, 64, 64, 64, 128, 0.4, 0, 0]],
            # 512x64 
            'msg2-sa1-cold': [str(x) for x in [0, 512, 128, 32, 3, 64, 64, 64, 128, 0.2, 0, 0]],
            # 512x128 
            'msg2-sa2-cold': [str(x) for x in [0, 512, 128, 64, 3, 128, 128, 128, 256, 0.4, 0, 0]],
            # 512x128 
            'msg2-sa3-cold': [str(x) for x in [0, 512, 128, 128, 3, 128, 128, 128, 256, 0.8, 0, 0]],
        },
        'histogram': {
            # N, warm
            'medium': [str(x) for x in [1 * 1024 * 1024 / 4, 1]],
            'large': [str(x) for x in [48 * 1024 * 1024 / 4, 1]],
            'large-cold': [str(x) for x in [48 * 1024 * 1024 / 4, 0]],
        }
    }

    def __init__(self, benchmark_args, benchmark_name, src_path):
        self.cwd = os.getcwd()
        self.src_path = src_path
        self.suite_path = src_path
        while os.path.basename(self.suite_path) != 'GemForgeMicroSuite':
            self.suite_path = os.path.dirname(self.suite_path)
        self.benchmark_name = benchmark_name
        self.source = f'{os.path.basename(src_path)}.c'
        self.graph_utils_source = '../gfm_graph_utils.c'
        self.stream_whitelist_fn = os.path.join(
            self.src_path, 'stream_whitelist.txt')

        self.value_type = 'VALUE_TYPE_FLOAT'
        if '_int32' in self.benchmark_name:
            self.value_type = 'VALUE_TYPE_INT32'
        elif '_int16' in self.benchmark_name:
            self.value_type = 'VALUE_TYPE_INT16'
        elif '_int8' in self.benchmark_name:
            self.value_type = 'VALUE_TYPE_INT8'
        self.is_omp = self.benchmark_name.startswith('omp_')
        self.is_avx512 = 'avx' in self.benchmark_name
        self.is_graph = os.path.basename(
            os.path.dirname(self.src_path)) == 'graph'
        self.n_thread = benchmark_args.options.input_threads

        self.is_variant_input = False
        self.variant_input_sizes = None
        for stem in GemForgeMicroBenchmark.INPUT_SIZE:
            if stem in self.benchmark_name:
                self.is_variant_input = True
                self.variant_input_sizes = GemForgeMicroBenchmark.INPUT_SIZE[stem]
                self.stem = stem

        self.work_items = -1
        if self.benchmark_name == 'omp_page_rank':
            # One iteration, two kernels.
            self.work_items = 2

        # Create the result dir out of the source tree.
        self.work_path = os.path.join(
            C.GEM_FORGE_RESULT_PATH, 'gfm', self.benchmark_name
        )
        Util.mkdir_chain(self.work_path)

        super(GemForgeMicroBenchmark, self).__init__(benchmark_args)

    def get_name(self):
        return 'gfm.{b}'.format(b=self.benchmark_name)

    def get_sim_input_args(self, input_name):
        base_input, _ = self.decompose_input_name(input_name)
        if self.is_variant_input:
            input_sizes = self.variant_input_sizes
            if base_input not in input_sizes:
                print(f'{self.benchmark_name} Missing Input Size {input_name} {base_input}')
                assert(False)
            return input_sizes[base_input]
        return list()

    def get_links(self):
        links = [
            f'-L{C.AFFINITY_ALLOC_LIB_PATH}',
            f'-lAffinityAllocGemForgeStatic',
        ]
        if self.is_omp:
            links += [
                '-lomp',
                '-lpthread',
                '-Wl,--no-as-needed',
                '-ldl',
            ]
        return links

    def get_args(self, input_name):
        base_input, _ = self.decompose_input_name(input_name)
        args = list()
        if self.is_omp or self.is_variant_input:
            args.append(str(self.n_thread))
            if self.is_graph:
                graphs = os.path.join(os.getenv('BENCHMARK_PATH'), 'graphs')
                suffix = 'wbin' if self.benchmark_name.startswith(
                    'omp_sssp_') else 'bin'
                args.append(os.path.join(graphs, '{i}.{s}'.format(
                    i=base_input, s=suffix)))
        args += self.get_sim_input_args(input_name)
        return args

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
            'stencil2d_hotspot',
        ]
        if self.benchmark_name in avx512_workloads or self.is_avx512:
            flags.append('-mavx512f')
            flags.append('-ffast-math')
            if self.value_type in ['VALUE_TYPE_INT16', 'VALUE_TYPE_INT8']:
                flags.append('-mavx512bw')
        if self.benchmark_name.endswith('histogram_avx'):
            flags.append('-mavx512dq')
            flags.append('-mavx512vl')
        if 'pntnet2' in self.benchmark_name:
            # Disable SLP vectorizer for the PointNet2 (as it vectorizes furthestSample).
            flags.append('-fno-slp-vectorize')
        return flags

    def get_sim_input_name(self, sim_input):
        # Only these workloads has sim_input_name.
        sim_name = f'thread{self.n_thread}'
        if self.is_graph or self.is_variant_input:
            sim_name = f'{sim_input}.{sim_name}'
        return sim_name

    OMP_GRAPH_FUNC_SUFFIX = {
        'omp_bfs': [''],
        'omp_bfs_queue': [''],
        'omp_page_rank': ['', '.1'],
        'omp_sssp_bellman': [''],
        'omp_dwt2d53': ['', '.10', '.8', '.9'],
        'omp_dwt2d53_avx': ['', '.10', '.8', '.9'],
        # 'omp_mm_inner_avx': ['', '.7'],
    }

    def get_trace_func(self):
        funcs = []
        if 'kmeans_cp' in self.benchmark_name:
            funcs = ['accCenter', 'rdcCenter', 'normCenter']
            funcs.append('.omp_outlined.' if self.is_omp else 'computeDist')
        elif 'kmeans_outer' in self.benchmark_name:
            funcs = ['rdcCenter', 'normCenter']
            funcs.append('.omp_outlined.' if self.is_omp else 'computeDist')
            funcs.append('.omp_outlined..8' if self.is_omp else 'findMinCenter')
            funcs.append('.omp_outlined..9' if self.is_omp else 'accCenter')
            if 'trans' in self.benchmark_name:
                funcs.append('transpose_row')

        elif 'dwt2d53' in self.benchmark_name:
            if self.is_omp:
                funcs = ['.omp_outlined.', 'repack']
            else:
                funcs = ['foo', 'repack']

        elif 'pointnet' in self.benchmark_name:
            if self.benchmark_name == 'omp_pointnet_gather_avx':
                funcs = ['.omp_outlined.']
            elif self.benchmark_name.find('pointnet_fused') == -1:
                assert(not self.is_omp)
                if self.benchmark_name.find('outer') != -1:
                    funcs = ['gather', 'layer_outer']
                elif self.benchmark_name.find('inner') != -1:
                    funcs = ['gather', 'layer_inner']
                else:
                    funcs = ['gather']
                if 'trans' in self.benchmark_name:
                    funcs += ['transpose_row', 'transpose_col']
            else:
                # Fused.
                funcs = ['gather', 'mlp', 'writeback']
        elif 'pntnet2' in self.benchmark_name:
            if self.is_omp:
                # This is the baseline we don't care.
                if self.benchmark_name == 'omp_pntnet2_inner_avx':
                    # sample, ball query, gather, layer inner, aggregate, copy, fc
                    funcs = ['computeMinDistTo', 'computeDistTo', '.omp_outlined..12', '.omp_outlined..13', '.omp_outlined..14', '.omp_outlined..15', '.omp_outlined..17']
                elif self.benchmark_name == 'omp_pntnet2_mlp_inner_avx':
                    funcs = ['.omp_outlined..13']
                else:
                    funcs = []
            else:
                if 'sample' in self.benchmark_name:
                    funcs = ['computeMinDistTo']
                elif 'agg' in self.benchmark_name:
                    funcs = ['aggregateMaxFeature']
                elif 'ball_query' in self.benchmark_name:
                    funcs = ['computeDistTo']
                elif 'mlp' in self.benchmark_name:
                    if 'outer' in self.benchmark_name:
                        funcs = ['layer_outer']
                    else:
                        funcs = ['layer_inner']
                    if 'trans' in self.benchmark_name:
                        funcs += ['transpose_row', 'transpose_col']
                else:
                    if 'outer' in self.benchmark_name:
                        funcs = ['computeMinDistTo', 'computeDistTo', 'gather', 'layer_outer', 'aggregateMaxFeature']
                    else:
                        funcs = ['computeMinDistTo', 'computeDistTo', 'gather', 'layer_inner', 'aggregateMaxFeature']
                    if 'trans' in self.benchmark_name:
                        funcs += ['transpose_row', 'transpose_col']
        elif self.is_omp:
            if self.benchmark_name in GemForgeMicroBenchmark.OMP_GRAPH_FUNC_SUFFIX:
                suffixes = GemForgeMicroBenchmark.OMP_GRAPH_FUNC_SUFFIX[self.benchmark_name]
                funcs = ['.omp_outlined.' + suffix for suffix in suffixes]
            else:
                funcs = ['.omp_outlined.']
        else:
            funcs = ['foo']
        return Benchmark.ROI_FUNC_SEPARATOR.join(funcs)

    def get_lang(self):
        return 'C'

    def get_exe_path(self):
        # Execute in the original src folder.
        return self.src_path

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
            f'-DVALUE_TYPE={self.value_type}',
            # '-fno-unroll-loops',
            # '-fno-vectorize',
            # '-fno-slp-vectorize',
            # '-ffp-contract=off',
            '-stream-specialize',
            '-mllvm',
            '-loop-unswitch-threshold=1',
            # '-mllvm',
            # '-opt-bisect-limit=235',
            '-I{GFM_INC}'.format(GFM_INC=self.suite_path),
        ] + self.get_extra_compile_flags()
        no_unroll_workloads = [
            'omp_bfs',
            'omp_page_rank',
            'omp_array_sum_avx',
            'omp_dot_prod_avx',
            'omp_vec_add_avx',
            'omp_stencil1d_avx',
            'omp_gaussian_elim',
            'omp_link_list',
            'gaussian_elim',
            'dwt2d53',
            'omp_dwt2d53',
            'mm_outer',
            'omp_mm_outer_avx',
            'omp_mm_inner_avx',
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
                f'-I{C.GEM5_INCLUDE_DIR}',
                f'-I{C.AFFINITY_ALLOC_INC_PATH}',
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
        if self.stem == 'mm_outer':
            # It takes for ever to finish mm_outer
            self.work_items = 2
        if self.work_items != -1:
            flags.append(
                '--work-end-exit-count={v}'.format(v=self.work_items),
            )
        if self.is_variant_input:
            yield_ns = 4000
            if 'pntnet2' in self.benchmark_name:
                yield_ns = 4000
            flags.append(
                f'--cpu-yield-lat={yield_ns}ns',
            )
        return flags

    def get_gem5_mem_size(self):
        if not self.is_omp:
            return '128MB'
        return None


class GemForgeMicroSuite:

    def tryAddBenchmark(self, benchmark_args, benchmark_name, abs_path):
        suite_benchmark_name = f'gfm.{benchmark_name}'
        if benchmark_args.options.benchmark:
            if suite_benchmark_name not in benchmark_args.options.benchmark:
                # Ignore benchmark not required.
                return
        print(f'Add {suite_benchmark_name}')
        self.benchmarks.append(
            GemForgeMicroBenchmark(benchmark_args, benchmark_name, abs_path))

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
                    benchmark_name = f'{item}'
                    self.tryAddBenchmark(benchmark_args, benchmark_name, abs_path)
                    # Also try int value type version.
                    for value_type in ['int32', 'int16', 'int8', 'fp16']:
                        variant_benchmark_name = f'{item}_{value_type}'
                        self.tryAddBenchmark(
                            benchmark_args, variant_benchmark_name, abs_path)
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
