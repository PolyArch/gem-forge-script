#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gfm.acc_gen_mm_M2048_N2048_K2048_amx,'
SimInput=''
# SimInput+='large,'
SimInput+='large-cold'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

# RubyConfig=8x8c
RubyConfig=8x8m4x4
Threads=1
Parallel=100

StreamTransform=''
StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
    # --transform-debug StreamLoopEliminator 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local o8_zen2=ss/ruby/uno/o8.cache-32kB-512kB-4MB.${rubyc}.c-gb-fifo
    local o8_sapphire_rapids=ss/ruby/uno/o8-sapphire-rapids.${rubyc}.c-gb-fifo
    local all_sim=''
    all_sim+=$o8_sapphire_rapids.fltsc-cmp-snuca-strnd,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug LLCRubyStream 2>&1 | tee /benchmarks/cmp.log
        # --gem5-variant fast \
        # --perf-command \
        # --gem5-debug ISAStreamEngine,StreamEngine,StreamBase,LLCRubyStream,MLCRubyStream | tee /benchmarks/cmp-cache.log
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel