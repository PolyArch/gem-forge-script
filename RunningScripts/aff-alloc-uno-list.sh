#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gap.pr_push_adj_aff,'
Benchmark+='gap.pr_push_adj_uno_aff,'
# Benchmark+='gap.pr_pull_adj_aff,'
Benchmark+='gap.pr_pull_adj_uno_aff,'
# Benchmark+='gap.bfs_push_adj_aff_sf,'
# Benchmark+='gap.bfs_push_adj_uno_aff_sf,'
# Benchmark+='gap.bfs_pull_adj_aff,'
# Benchmark+='gap.bfs_pull_nobrk_adj_aff,'
# Benchmark+='gap.sssp_adj_aff_sf_delta1,'
# Benchmark+='gap.sssp_adj_aff_sf_delta2,'
# Benchmark+='gap.sssp_adj_aff_sf_delta4,'
# Benchmark+='gap.sssp_adj_aff_sf_delta8,'
# Benchmark+='gap.sssp_adj_aff_sf_delta16,'
# Benchmark+='gap.sssp_adj_aff_sf_delta32,'
SimInput=''
# SimInput+=',krn17-k16.aff-random'
# SimInput+=',krn17-k16.aff-min-hops'
# SimInput+=',krn17-k16.aff-min-load'
# SimInput+=',krn17-k16.aff-hybrid'
# SimInput+=',krn17-k16.aff-delta'
# SimInput+=',krn17-k16.aff-hybrid1'
# SimInput+=',krn17-k16.aff-hybrid3'
# SimInput+=',krn17-k16.aff-hybrid5'
# SimInput+=',krn17-k16.aff-hybrid7'
# SimInput+=',krn17-k16.aff-hybrid9'
# SimInput+=',krn17-k16.aff-hybrid11'
# SimInput+=',krn17-k16.aff-hybrid13'
SimInput+=',krn17-k16-rnd64.aff-random'
SimInput+=',krn17-k16-rnd64.aff-min-hops'
SimInput+=',krn17-k16-rnd64.aff-min-load'
SimInput+=',krn17-k16-rnd64.aff-hybrid5'
SimInput+=',uni17-k16-rnd64.aff-random'
SimInput+=',uni17-k16-rnd64.aff-min-hops'
SimInput+=',uni17-k16-rnd64.aff-min-load'
SimInput+=',uni17-k16-rnd64.aff-hybrid5'
# SimInput+=',roadNet-TX-rnd64.aff-random'
# SimInput+=',roadNet-TX-rnd64.aff-min-hops'
# SimInput+=',roadNet-TX-rnd64.aff-min-load'
# SimInput+=',roadNet-TX-rnd64.aff-hybrid5'
# SimInput+=',web-BerkStan-rnd64.aff-random'
# SimInput+=',web-BerkStan-rnd64.aff-min-hops'
# SimInput+=',web-BerkStan-rnd64.aff-min-load'
# SimInput+=',web-BerkStan-rnd64.aff-hybrid5'
# SimInput+=',krn17-k16.aff-delta1'
# SimInput+=',krn17-k16.aff-delta3'
# SimInput+=',krn17-k16.aff-delta5'
# SimInput+=',krn17-k16.aff-delta7'
# SimInput+=',krn17-k16.aff-delta9'
# SimInput+=',krn17-k16.aff-delta11'
# SimInput+=',krn17-k16.aff-delta13'
# SimInput+=',krn14-k16.aff-hybrid'
# SimInput+=',krn10-k4.aff-random'
# SimInput+=',krn10-k4.aff-delta'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace 

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
Parallel=32
sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=$o8,$o8.bingo-l2pf
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
#     --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StreamLoopEliminator,StaticStreamLoopBoundBuilder,BasicBlockBranchDataGraph 2>&1 | tee /benchmarks/shit.log

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
    # all_sim+=$o8.flts-mc,
    # all_sim+=$o8.fltsc-cmp,
    # all_sim+=$o8.fltsc-cmp-snuca,
    all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
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
        # --gem5-debug StreamEngine,StreamElement,StreamBase,StreamRegion,ExecFunc 2>&1 | tee /benchmarks/core.log
        # --gem5-debug ProtocolTrace,MLCRubyStream,LLCRubyStream --gem5-debug-start 25509906500 2>&1 | tee /benchmarks/llc.log
        # --perf-command \
}
# run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 