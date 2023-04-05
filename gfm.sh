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
# Benchmark+='gfm.omp_mm_inner_tile8x8x256_avx,'
# Benchmark+='gfm.omp_conv3d_zxy_obybxyxi_outer_32x32_avx,'
# Benchmark+='gfm.omp_conv3d_zxy_fbybx_oxyxi_outer_32x32_avx,'
# Benchmark+='gfm.omp_kmeans_avx,'
# Benchmark+='gfm.omp_kmeans_outer_split_avx,'
# Benchmark+='gfm.omp_pointnet_fused_inner_avx,'
# Benchmark+='gfm.omp_pointnet_fused_outer_avx,'
# Benchmark+='gfm.dwt2d53,'
# Benchmark+='gfm.stencil1d,'
# Benchmark+='gfm.stencil2d,'
# Benchmark+='gfm.stencil3d,'
# Benchmark+='gfm.gaussian_elim,'
# Benchmark+='gfm.conv2d,'
# Benchmark+='gfm.mm_outer,'
# Benchmark+='gfm.mm_inner,'
# Benchmark+='gfm.mm_inner_pum_tile16,'
# Benchmark+='gfm.mm_inner_pum_tile32,'
# Benchmark+='gfm.mm_inner_pum_tile64,'
# Benchmark+='gfm.mm_inner_pum_tile128,'
# Benchmark+='gfm.mm_inner_pum_tile256,'
# Benchmark+='gfm.mm_inner_pum_tile512,'
# Benchmark+='gfm.conv3d_xyz_ioyx_outer,'
# Benchmark+='gfm.kmeans_cp_pum_avx,'
# Benchmark+='gfm.kmeans_outer_pum_avx,'
# Benchmark+='gfm.pointnet_inner_pum_avx,'
# Benchmark+='gfm.pointnet_outer_pum_avx,'
# Benchmark+='gfm.mm_lmn,'
# Benchmark+='gfm.kmeans_inner_pum_avx,'
# Benchmark+='gfm.pointnet_outer_transrr_pum_avx,'
# Benchmark+='gfm.kmeans_outer_split_trans_pum_avx,'
# Benchmark+='gfm.mm_outer_int16,'
# Benchmark+='gfm.omp_array_sum_avx,'
# Benchmark+='gfm.omp_vec_add_avx,'
# Benchmark+='gfm.array_sum,'
Benchmark+='gfm.vec_add_avx,'
# Benchmark='--suite gap'
# SimInput=small-cold,medium-cold,large-cold,small,medium,large,tiny,tiny-cold,teeny,teeny-cold
# SimInput=tiny,small,medium,large
# SimInput=small-cold
# SimInput=strnd,strnd-cold
SimInput=large
# SimInput=small-cold,small
# SimInput=duality-cold
Threads=64

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
# RubyConfig=2400MHz.6x3c1x2
Parallel=80
sim_replay_prefix=replay/ruby/single
i4=$sim_replay_prefix/i4.tlb.${RubyConfig}
o4=$sim_replay_prefix/o4.tlb.${RubyConfig}
o8=$sim_replay_prefix/o8.tlb.${RubyConfig}
# sim_replay=$o8,$o8.bingo-l2pf
sim_replay=$o8.bingo-l2pf
# sim_replay=$o8.llc2MB.bingo-l2pf
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
# --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel 
    # --gem5-debug DRAMsim3 --gem5-debug-start 15502083420 | tee gfm.log

StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp
# StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StaticStreamRegionAnalyzer,StaticIndVarStream 2>&1 | tee /benchmarks/gfm-new.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8_llc2MB.fltsc-cmp-pum-strnd,
    # all_sim+=$o8,
    all_sim+=$o8.flts,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug MLCStreamPUM 2>&1 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM,MLCRubyStream | tee /benchmarks/gfm-new.log
        # --gem5-debug ISAStreamEngine,StreamEngine --gem5-debug-start 16936500 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM | tee /benchmarks/gfm-new.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 4228029500 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamEngine,StreamBase,StreamFloatController  | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamAlias,O3CPUDelegator,LSQUnit,StreamBase,StreamEngine,StreamElement | tee hhh.log
        # --gem5-debug RubyStreamLife | tee bfs.log &
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel