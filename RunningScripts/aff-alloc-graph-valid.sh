#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gap.sssp_sf_delta1,'
# Benchmark+='gap.pr_pull,'
# Benchmark+='gap.pr_push,'
# Benchmark+='gap.bfs_push_sf,'
# Benchmark+='gap.bfs_push_check,'
# Benchmark+='gap.bfs_pull,'
# Benchmark+='gap.bfs_pull_nobrk,'
# Benchmark+='gap.sssp_adj_aff_sf_delta1,'
# Benchmark+='gap.bfs_pull_nobrk_adj_aff,'
# Benchmark+='gap.pr_push_adj_aff,'
# Benchmark+='gap.pr_pull_adj_aff,'
# Benchmark+='gap.bfs_push_adj_aff_sf,'
# Benchmark+='gap.bfs_pull_adj_aff,'
# Benchmark+='gap.bfs,'
SimInput=''
# SimInput+=',krn18-k16'
SimInput+=',krn17-k16-rnd64'
# SimInput+=',krn16-k16'
# SimInput+=',krn15-k16'
# SimInput+=',krn14-k16'
# SimInput+=',krn10-k16'
# SimInput+=',krn10-k4'
# SimInput+=',krn17-k16.aff-min-hops'
# SimInput+=',krn17-k16.aff-min-load'
# SimInput+=',krn17-k16.aff-random'
# SimInput+=',krn17-k16.aff-hybrid'
# SimInput+=',krn17-k16.aff-delta'
# SimInput+=',krn14-k16.aff-min-hops'
# SimInput+=',krn14-k16.aff-min-load'
# SimInput+=',krn14-k16.aff-random'
# SimInput+=',krn10-k4.aff-min-hops'
# SimInput+=',krn10-k4.aff-min-load'
# SimInput+=',krn10-k4.aff-random'
# SimInput+=',krn10-k4.aff-hybrid'


SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
# RubyConfig=4x4c
# Threads=1
# RubyConfig=2x2c
# Threads=4
Parallel=64
sim_replay_prefix=base/ruby/uno
i4=$sim_replay_prefix/i4.${RubyConfig}
o4=$sim_replay_prefix/o4.${RubyConfig}
o8=$sim_replay_prefix/o8.${RubyConfig}
# sim_replay=$i4,$i4.bingo-l2pf
# sim_replay+=,$o4,$o4.bingo-l2pf
sim_replay=$o8,$o8.bingo-l2pf
# sim_replay=$o8
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
#     --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel

# StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp
StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StaticStreamRegionAnalyzer,BasicBlockBranchDataGraph 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local tm=ss/ruby/uno/tm.$rubyc.c-fifo
    local o8_link=stream/ruby/single/o8.$rubyc-link.c
    local all_sim=''
    # all_sim+=$o8,
    all_sim+=$o8-cmp,
    # all_sim+=$o8.flts-mc,
    # all_sim+=$o8.fltsc-cmp,
    # all_sim+=$o8.fltsc-cmp-snuca,
    # all_sim+=$o8.fltsc-cmp-snuca-dist,
    # all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    # all_sim+=$o8.fltsc-cmp-snuca-idea-ind-req,
    # all_sim+=$o8.fltsc-cmp-snuca-test,
    # all_sim+=$o8.fltsc-cmp-snuca-rmtcfg-test,
    # all_sim+=$o8.fltsc-cmp-snuca-rmtcfg-midway,
    # all_sim+=$o8.inoc-gussa.fltsc-cmp,
    # all_sim+=$o8.inoc-all.fltsc-cmp,
    # all_sim+=$o8.inoc-all-il3.fltsc-cmp,
    # all_sim+=$o8.inoc-sa.fltsc-cmp,
    # all_sim+=$o8.inoc-sa.fltsc-cmp-snuca,
    # all_sim+=$o8.inoc-sa.fltsc-cmp-snuca-rmtcfg,
    # all_sim+=$o8.inoc-sa.fltsc-cmp-rmtcfg,
    # all_sim+=$o8.inoc-sa.fltsc-cmp-snuca-elem,
    # all_sim+=$o8.fltsc-cmp-sync,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug ProtocolTrace,MLCRubyStream,LLCRubyStream --gem5-debug-start 25509906500 2>&1 | tee /benchmarks/llc.log
        # --gem5-debug StreamEngine,StreamElement,StreamBase,StreamRegion 2>&1 | tee /benchmarks/core.log
        # --perf-command \
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 