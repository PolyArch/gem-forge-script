#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gap.sssp_sf_delta1,'
Benchmark+='gap.pr_pull,'
Benchmark+='gap.pr_push,'
Benchmark+='gap.bfs_push_sf,'
Benchmark+='gap.bfs_pull,'
# Benchmark+='gap.bfs_pull_nobrk,'
SimInput=''
# SimInput+=',krn18-k16'
SimInput+=',krn17-k16'
# SimInput+=',krn16-k16'
# SimInput+=',krn15-k16'
# SimInput+=',krn14-k16'
# SimInput+=',krn10-k16'
# SimInput+=',krn10-k4'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
Parallel=64
sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=$o8,$o8.bingo-l2pf
# sim_replay=$o8
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
#     --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StaticStreamRegionAnalyzer,BasicBlockBranchDataGraph 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8.fltsc-cmp-snuca,
    all_sim+=$o8.fltsc-cmp-snuca-dist-idea-csr,
    # all_sim+=$o8.fltsc-cmp-snuca-idea-csr,
    # all_sim+=$o8.fltsc-cmp-snuca-idea-ind-req,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug StreamNUCAManager 2>&1 | tee /benchmarks/core.log
        # --perf-command \
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 