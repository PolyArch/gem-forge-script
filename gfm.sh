#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b gfm.vec_add_avx'
# Benchmark='-b gfm.omp_gaussian_elim_avx'
# Benchmark='-b gfm.mm_outer'
# Benchmark='-b gfm.dwt2d53,gfm.stencil1d_avx,gfm.stencil2d_avx,gfm.stencil3d_avx'
# Benchmark='-b gfm.omp_dwt2d53_avx,gfm.omp_stencil1d_avx,gfm.omp_stencil2d_avx,gfm.omp_stencil3d_avx'
# Benchmark='-b gfm.stencil1d_avx,gfm.stencil2d_avx,gfm.stencil3d_avx'
# Benchmark='-b gfm.dwt2d53,gfm.stencil1d_avx,gfm.stencil2d_avx,gfm.stencil3d_avx,gfm.gaussian_elim,gfm.mm_outer,gfm.mm_inner,gfm.conv2d'
# Hotspot is not working with strand yet.
# Benchmark='-b rodinia.hotspot-avx512-fix-fp32'
# Benchmark='--suite gap'
# SimInput=small
SimInput=large
Threads=64

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
# RubyConfig=8x8t4x4
Parallel=100
sim_replay_prefix=replay/ruby/single
i4=$sim_replay_prefix/i4.tlb.${RubyConfig}
o4=$sim_replay_prefix/o4.tlb.${RubyConfig}
o8=$sim_replay_prefix/o8.tlb.${RubyConfig}
sim_replay=$o8,$o8.bingo-l2pf
# sim_replay=$o8
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
#     --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel 
    # --gem5-debug DRAMsim3 --gem5-debug-start 15502083420 | tee gfm.log

StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp
# StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StreamLoopEliminator

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    # local all_sim=$o8
    # local all_sim=$o8-cmp
    local all_sim=$o8.flts
    # local all_sim=$o8.fltsc-cmp-strnd
    # local all_sim=$o8.fltsc-cmp-pum
    # local all_sim=$o8.fltsc-cmp-pum-strnd
    # local all_sim=$o8.fltsc-cmp-pum,$o8.fltsc-cmp-pum-strnd
    # local all_sim=$o8.fltsc-cmp-pumm
    # local all_sim=$o8.fltsc-cmp-strnd,$o8.fltsc-cmp
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug MLCRubyStream,StreamPUM | tee /benchmarks/gfm.log
        # --gem5-debug StreamEngine --gem5-debug-start  | tee gfm.log
        # --gem5-debug IEW,LSQ,LSQUnit | tee iew.log
        # --gem5-debug StreamAlias,O3CPUDelegator,LSQUnit,StreamBase,StreamEngine,StreamElement | tee hhh.log
        # --gem5-debug RubyStreamLife | tee bfs.log &
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel
