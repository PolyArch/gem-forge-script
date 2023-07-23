#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='rodinia.streamcluster,'
# Benchmark+='mine.svm,'
# Benchmark+='gfm.omp_hash_join,'
# Benchmark+='gfm.omp_histogram_avx,'
# Benchmark+='gfm.omp_binary_tree,'
# Benchmark+='rodinia.pathfinder-avx512-nounroll,'
# Benchmark+='rodinia.hotspot-avx512-fix,'
# Benchmark+='rodinia.srad_v2-avx512-fix,'
# Benchmark+='rodinia.hotspot3D-avx512-fix-fuse,'
# New workloads.
# Benchmark+='gfm.omp_dwt2d53_avx,'
# Benchmark+='gfm.omp_gaussian_elim_avx,'
# Benchmark+='gfm.omp_conv2d_avx,'
# Benchmark+='gfm.omp_mm_outer_avx,'
# Benchmark+='gfm.omp_mm_inner_avx,'
# Benchmark+='gfm.omp_conv3d_zxy_oyxi_outer_tile_avx,'
# Benchmark+='gfm.omp_kmeans_avx,'
# Benchmark+='gfm.omp_pointnet_fused_inner_avx,'
# Benchmark+='gfm.omp_pointnet_fused_outer_avx,'
# Benchmark+='gfm.omp_kmeans_outer_split_avx,'
Benchmark+='gfm.omp_mm_inner_tile8x8x256_avx,'
SimInput=large
# SimInput=large-cold

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
Parallel=100
sim_replay_prefix=base/ruby/uno
i4=$sim_replay_prefix/i4.${RubyConfig}
o4=$sim_replay_prefix/o4.${RubyConfig}
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=''
sim_replay+=$i4,$o4,$o8,
sim_replay+=$i4.bingo-l2pf,$o4.bingo-l2pf,$o8.bingo-l2pf,
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
    --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel \
    # --no-job-log