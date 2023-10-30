#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gfm.omp_dwt2d53_avx,'
# Benchmark+='gfm.omp_stencil1d_avx,'
# Benchmark+='gfm.omp_stencil2d_avx,'
# Benchmark+='gfm.omp_stencil3d_avx,'
# Benchmark+='gfm.omp_gaussian_elim_avx,'
# Benchmark+='gfm.omp_conv2d_avx,'
# Benchmark+='gfm.omp_mm_outer_avx,'
# Benchmark+='gfm.omp_mm_inner_avx,'
# Benchmark+='gfm.omp_conv3d_zxy_oyxi_outer_tile_avx,'
# Benchmark+='gfm.omp_kmeans_avx,'
# Benchmark+='gfm.omp_pointnet_fused_inner_avx,'
# Benchmark+='gfm.omp_pointnet_fused_outer_avx,'
# Benchmark+='gfm.omp_kmeans_outer_split_avx,'
# Benchmark+='gfm.omp_mm_inner_tile2x2x1024_avx,'
# Benchmark+='gfm.omp_mm_inner_tile4x4x512_avx,'
# Benchmark+='gfm.omp_mm_inner_tile8x8x256_avx,'
# Benchmark+='gfm.omp_mm_inner_tile16x16x128_avx,'
# Benchmark+='gfm.omp_mm_inner_tile32x32x64_avx,'
# Benchmark+='gfm.dwt2d53,'
# Benchmark+='gfm.stencil1d,'
# Benchmark+='gfm.stencil2d,'
# Benchmark+='gfm.stencil3d,'
# Benchmark+='gfm.gaussian_elim,'
# Benchmark+='gfm.conv2d,'
# Benchmark+='gfm.mm_outer,'
# Benchmark+='gfm.mm_inner,'
# Benchmark+='gfm.mm_inner_pum_tile16,'
# Benchmark+='gfm.mm_inner_pum_tile64,'
# Benchmark+='gfm.mm_inner_pum_tile128,'
# Benchmark+='gfm.mm_inner_pum_tile256,'
# Benchmark+='gfm.mm_inner_pum_tile512,'
# Benchmark+='gfm.conv3d_xyz_ioyx_outer,'
# Benchmark+='gfm.kmeans_cp_pum_avx,'
# Benchmark+='gfm.kmeans_outer_pum_avx,'
# Benchmark+='gfm.pointnet_outer_pum_avx,'
# Benchmark+='gfm.pointnet_inner_pum_avx,'
# Benchmark+='gfm.omp_pointnet_gather_avx,'
# Benchmark='--suite gap'
# SimInput=tiny-cold,small-cold,medium-cold,large-cold
# SimInput=tiny,small,medium,large
SimInput=large-cold,large
# SimInput=large2x-cold,large2x
Threads=64

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
# RubyConfig=8x8c
RubyConfig=8x8t4x4
Parallel=40
sim_replay_prefix=replay/ruby/single
i4=$sim_replay_prefix/i4.tlb.${RubyConfig}
o4=$sim_replay_prefix/o4.tlb.${RubyConfig}
o8=$sim_replay_prefix/o8.tlb.${RubyConfig}
sim_replay=$o8,$o8.bingo-l2pf
# sim_replay=$o8
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
--sim-configs $sim_replay --input-threads $Threads -s -j $Parallel 
    # --gem5-debug DRAMsim3 --gem5-debug-start 15502083420 | tee gfm.log

# StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp
StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StreamLoopEliminator 2>&1 | tee /benchmarks/gfm-new.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=stream/ruby/single/i4.tlb.$rubyc.c
    local o4=stream/ruby/single/o4.tlb.$rubyc.c-gb-fifo
    local o8=stream/ruby/single/o8.tlb.$rubyc.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8,
    # all_sim+=$o8-cmp,
    # all_sim+=$o8.fltsc-cmp-iack,
    # all_sim+=$o8.fltsc-cmpv-strnd,
    all_sim+=$o8.fltsc-cmp-pum-strnd,
    # all_sim+=$o8.fltsc-cmp-pum-strnd-int,
    # all_sim+=$o8.fltsc-cmpv-strnd,$o8.fltsc-cmp-pum-strnd,
    # all_sim+=$o8.fltsc-cmp-pum-strnd-softcompile,
    # all_sim+=$o8.fltsc-cmp-pum,$o8.fltsc-cmp-pum-strnd,$o8.fltsc-cmp-pum-strnd-real,$o8.fltsc-cmp-pum-strnd-notile,$o8.fltsc-cmp-pum-strnd-softcompile,$o8.fltsc-cmp-pum-strnd-nocompile,$o8.fltsc-cmp-pum-strnd-nodfg,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug StreamNUCAManager,MLCStreamPUM | tee /benchmarks/gfm-new.log
        # --gem5-debug LLCRubyStream,MLCRubyStream | tee /benchmarks/gfm-new.log
        # --gem5-debug ISAStreamEngine,StreamEngine --gem5-debug-start 1200000000 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamEngine,StreamBase,StreamFloatController  | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamAlias,O3CPUDelegator,LSQUnit,StreamBase,StreamEngine,StreamElement | tee hhh.log
        # --gem5-debug RubyStreamLife | tee bfs.log &
}
# run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel