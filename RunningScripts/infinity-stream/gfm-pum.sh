#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gfm.dwt2d53,'
Benchmark+='gfm.stencil1d,'
Benchmark+='gfm.stencil2d,'
Benchmark+='gfm.stencil3d,'
Benchmark+='gfm.gaussian_elim,'
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
# SimInput=large-cold
# SimInput=large2x-cold,large2x
Threads=64

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

# RubyConfig=8x8c
RubyConfig=8x8t4x4
Parallel=40

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StreamLoopEliminator 2>&1 | tee /benchmarks/gfm-new.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    all_sim+=$o8.fltsc-cmp-pum-strnd,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug LLCRubyStream,MLCRubyStream | tee /benchmarks/gfm-new.log
        # --gem5-debug MLCStreamPUM,LLCStreamPUM,MLCRubyStream,LLCRubyStream,StreamEnd --gem5-debug-start 2437780000 --gem5-max-ticks 2500786000 | tee /benchmarks/gfm-new.log
        # --gem5-debug ISAStreamEngine,StreamEngine --gem5-debug-start 1200000000 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamEngine,StreamBase,StreamFloatController  | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamAlias,O3CPUDelegator,LSQUnit,StreamBase,StreamEngine,StreamElement | tee hhh.log
        # --gem5-debug RubyStreamLife | tee bfs.log &
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel