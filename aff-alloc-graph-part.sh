#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gap.sssp_check,'
# Benchmark+='gap.sssp_sf_delta1,'
# Benchmark+='gap.sssp_sf_delta2,'
# Benchmark+='gap.sssp_sf_delta4,'
# Benchmark+='gap.sssp_sf_delta8,'
# Benchmark+='gap.sssp_sf_delta16,'
# Benchmark+='gap.sssp_sf_delta32,'
# Benchmark+='gap.pr_push,'
# Benchmark+='gap.pr_pull,'
# Benchmark+='gap.bfs_push_sf,'
# Benchmark+='gap.bfs_pull,'
# Benchmark+='gap.bfs_pull_nobrk,'
# Benchmark+='gap.bfs_pull_nobrk_adj_aff,'
SimInput=''
# SimInput+=',krn18-k16'

# SimInput+=',krn15-k64-rnd64'
# SimInput+=',krn16-k32-rnd64'
# SimInput+=',krn18-k8-rnd64'
# SimInput+=',krn19-k4-rnd64'

# SimInput+=',twitch-gamers-rnd64'
# SimInput+=',ego-fb-rnd64'
# SimInput+=',ego-twitter-rnd64'
# SimInput+=',ego-gplus-rnd64'
# SimInput+=',soc-LiveJournal1-rnd64'
# SimInput+=',krn20-k2-rnd64'

# SimInput+=',twitch-gamers-ne64.part'
# SimInput+=',ego-gplus-ne64.part'

# SimInput+=',twitch-gamers-orig64.part'
# SimInput+=',ego-gplus-orig64.part'
# SimInput+=',twitch-gamers-orig64'
# SimInput+=',ego-gplus-orig64'

SimInput+=',krn17-k16-rnd64'
# SimInput+=',krn17-k16-rnd64.cold'


SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
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
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
    --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel

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
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8,
    # all_sim+=$o8.fltsc-cmp-snuca,
    all_sim+=$o8.fltsc-cmp-snuca-dist,
    # all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug StreamNUCAManager 2>&1 | tee /benchmarks/llc.log
        # --gem5-debug StreamEngine,StreamElement,StreamBase,StreamRegion 2>&1 | tee /benchmarks/core.log
        # --perf-command \
}
# run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 