#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='rodinia.streamcluster,'
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
# Benchmark+='gfm.omp_mm_inner_tile8x8x256_avx,'
SimInput=large
# SimInput=large-cold

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

RubyConfig=8x8c
Threads=64
Parallel=100

StreamTransform=stream/ex/static/so.store.cmp
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
    # --transform-debug StaticStreamRegionAnalyzer 2>&1 | tee shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local o8_link=stream/ruby/single/o8.tlb.$rubyc-link.c
    local all_sim=''
    all_sim+=$i4.fltsc-cmp-sync,$o4.fltsc-cmp-sync,$o8.fltsc-cmp-sync,
    all_sim+=$i4.fltsc-cmp,$o4.fltsc-cmp,$o8.fltsc-cmp,
    # all_sim+=$o8.inoc.fltsc-cmp,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug StreamBase,StreamEngine,StreamElement | tee /benchmarks/cmp.log
        # --gem5-debug ISAStreamEngine,StreamEngine,StreamBase,LLCRubyStream,MLCRubyStream --gem5-debug-start 82290072000 --gem5-max-ticks 82295572000 | tee /benchmarks/cmp-cache.log
        # --gem5-debug LLCRubyStream,MLCRubyStream | tee /benchmarks/cmp-cache.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 45820730500 --gem5-max-ticks 45830730500 | tee /benchmarks/cmp.log
        # --gem5-debug LLCRubyStream,MLCRubyStream,ISAStreamEngine,StreamEngine,StreamBase --gem5-debug-start 28672993500 | tee /benchmarks/cmp.log
}
RubyConfig=8x8c
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel