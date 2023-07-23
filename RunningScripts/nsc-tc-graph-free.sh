#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gap.sssp,'
Benchmark+='gap.sssp_sf_delta1,'
Benchmark+='gap.pr_pull_shuffle,'
Benchmark+='gap.pr_push,'
Benchmark+='gap.bfs_pull_shuffle_nobrk,'
Benchmark+='gap.bfs_push,'
Benchmark+='gap.bfs_push_sf,'
SimInput=krn18-k16
# SimInput=krn18-k16-cold
# SimInput=krn10-k4

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

RubyConfig=8x8c
Threads=64
Parallel=100

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
    # --transform-debug StaticStreamRegionAnalyzer 2>&1 | tee shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c-gb-fifo
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local o8_link=stream/ruby/single/o8.tlb.$rubyc-link.c
    local all_sim=''
    # all_sim+=$o8.fltsc-cmp,
    # all_sim+=$i4.fltsc-cmp,$o4.fltsc-cmp,$o8.fltsc-cmp,
    all_sim+=$i4.fltsc-cmp-snuca,
    all_sim+=$o4.fltsc-cmp-snuca,
    all_sim+=$o8.fltsc-cmp-snuca,
    # all_sim+=$i4.fltsc-cmp-snuca-rmtcfg,
    # all_sim+=$o4.fltsc-cmp-snuca-rmtcfg,
    # all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    # all_sim+=$o8.inoc.fltsc-cmp,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug IEW,Commit,ISAStreamEngine,ROB --gem5-debug-start 456170000 2>&1 | tee /benchmarks/o3.log
        # --gem5-debug ISAStreamEngine,StreamBase,StreamEngine,StreamElement --gem5-debug-start 447179500 2>&1 | tee /benchmarks/core.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 10753912500 2>&1 | tee /benchmarks/cmp-cache.log
        # --gem5-debug ISAStreamEngine,StreamEngine,StreamBase,LLCRubyStream,MLCRubyStream --gem5-debug-start 82290072000 --gem5-max-ticks 82295572000 | tee /benchmarks/cmp-cache.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 45820730500 --gem5-max-ticks 45830730500 | tee /benchmarks/cmp.log
        # --gem5-debug LLCRubyStream,MLCRubyStream,ISAStreamEngine,StreamEngine,StreamBase --gem5-debug-start 28672993500 | tee /benchmarks/cmp.log
}
RubyConfig=8x8c
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel