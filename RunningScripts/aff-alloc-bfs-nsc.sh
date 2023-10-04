#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gap.bfs_push_sf,'
Benchmark+='gap.bfs_pull,'
# Benchmark+='gap.bfs_scout_sf_test,'
# Benchmark+='gap.bfs_scout_sf,'
# Benchmark+='gap.pr_push,'
# Benchmark+='gap.pr_pull,'
# Benchmark+='gap.sssp_sf_delta1,'


SimInput=''

# SimInput+=',ego-gplus-rnd64'
# SimInput+=',twitch-gamers-rnd64'

# SimInput+=',krn15-k64-rnd64'
# SimInput+=',krn16-k32-rnd64'
# SimInput+=',krn17-k16-rnd64'
# SimInput+=',krn18-k8-rnd64'
# SimInput+=',krn19-k4-rnd64'
# SimInput+=',krn20-k2-rnd64'

# SimInput+=',krn18-k16-rnd64'
# SimInput+=',krn19-k16-rnd64'
SimInput+=',krn20-k16-rnd64'

# SimInput+=',krn14-k8-rnd64'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

RubyConfig=8x8c
Threads=64
Parallel=64

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StaticStreamRegionAnalyzer 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    all_sim+=$o8.fltsc-cmp-snuca-dist,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug LLCRubyStream,ProtocolTrace --gem5-debug-start 22925534500 --gem5-max-ticks 23100000001 2>&1 | tee /benchmarks/proto.log
        # --gem5-variant fast \
        # --perf-command \
        # --gem5-debug StreamLoopBound 2>&1 | tee /benchmarks/llc.log \
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 