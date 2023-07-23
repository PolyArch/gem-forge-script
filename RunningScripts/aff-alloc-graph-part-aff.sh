#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gap.sssp_sf_delta1,'
# Benchmark+='gap.sssp_sf_delta2,'
# Benchmark+='gap.sssp_sf_delta4,'
# Benchmark+='gap.sssp_sf_delta8,'
# Benchmark+='gap.sssp_sf_delta16,'
# Benchmark+='gap.sssp_sf_delta32,'
# Benchmark+='gap.pr_pull,'
# Benchmark+='gap.pr_push,'
# Benchmark+='gap.bfs_push_sf,'
# Benchmark+='gap.bfs_pull,'
# Benchmark+='gap.bfs_pull_nobrk,'
# Benchmark+='gap.sssp_adj_aff_sf_delta1,'
# Benchmark+='gap.sssp_adj_aff_sf_delta2,'
# Benchmark+='gap.sssp_adj_aff_sf_delta4,'
# Benchmark+='gap.sssp_adj_aff_sf_delta8,'
# Benchmark+='gap.sssp_adj_aff_sf_delta16,'
# Benchmark+='gap.sssp_adj_aff_sf_delta32,'
# Benchmark+='gap.bfs_pull_nobrk_adj_aff,'
# Benchmark+='gap.pr_push_adj_aff,'
# Benchmark+='gap.pr_pull_adj_aff,'
# Benchmark+='gap.bfs_push_adj_aff_sf,'
# Benchmark+='gap.bfs_pull_adj_aff,'
# Benchmark+='gap.pr_push_adj_s_aff,'
# Benchmark+='gap.pr_push_adj_uno_aff,'
# Benchmark+='gap.pr_pull_adj_uno_aff,'
# Benchmark+='gap.bfs_push_adj_uno_aff_sf,'
Benchmark+='gap.bfs_pull_adj_uno_aff,'
# Benchmark+='gap.bc_adj_uno_aff_sq,'
# Benchmark+='gap.sssp_adj_uno_aff_sf_delta1,'

# Benchmark+='gap.pr_push_adj_uno_aff_thd,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn16,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn32,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn64,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn128,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn256,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn512,'
# Benchmark+='gap.pr_push_adj_uno_aff_dyn1024,'
SimInput=''

# SimInput+=',uni17-k16-rnd64.aff-hybrid5'
# SimInput+=',roadNet-TX-rnd64.aff-hybrid5'
# SimInput+=',web-BerkStan-rnd64.aff-hybrid5'
# SimInput+=',ego-fb-rnd64.aff-hybrid5'
# SimInput+=',ego-twitter-rnd64.aff-hybrid5'

# SimInput+=',uni17-k16-rnd64.aff-random'
# SimInput+=',roadNet-TX-rnd64.aff-random'
# SimInput+=',web-BerkStan-rnd64.aff-random'
# SimInput+=',ego-fb-rnd64.aff-random'
# SimInput+=',ego-twitter-rnd64.aff-random'

# SimInput+=',roadNet-TX-rnd64.aff-min-hops'
# SimInput+=',web-BerkStan-rnd64.aff-min-hops'
# SimInput+=',ego-fb-rnd64.aff-min-hops'
# SimInput+=',ego-twitter-rnd64.aff-min-hops'

# SimInput+=',ego-gplus-rnd64.aff-hybrid5'
# SimInput+=',ego-gplus-rnd64.aff-min-hops'
# SimInput+=',ego-gplus-rnd64.aff-random'

# SimInput+=',twitch-gamers-rnde64.aff-hybrid5'
# SimInput+=',twitch-gamers-rnde64.aff-min-hops'
# SimInput+=',twitch-gamers-rnde64.aff-random'
# SimInput+=',twitch-gamers-rnd64.aff-hybrid5'
# SimInput+=',twitch-gamers-rnd64.aff-min-hops'
# SimInput+=',twitch-gamers-rnd64.aff-random'

# SimInput+=',soc-LiveJournal1-rnd64.aff-hybrid5'
# SimInput+=',soc-LiveJournal1-rnd64.aff-min-hops'
# SimInput+=',soc-LiveJournal1-rnd64.aff-random'

SimInput+=',krn17-k16-rnd64.aff-hybrid5'
# SimInput+=',krn17-k16-rnd64.aff-min-hops'
# SimInput+=',krn17-k16-rnd64.aff-random'
# SimInput+=',krn17-k16-rnd64.aff-hybrid5.cold'
# SimInput+=',krn17-k16-rnd64.aff-min-hops.cold'
# SimInput+=',krn17-k16-rnd64.aff-random.cold'

# SimInput+=',krn14-k8-rnd64.aff-hybrid5'

# SimInput+=',krn15-k64-rnd64.aff-random'
# SimInput+=',krn15-k64-rnd64.aff-min-hops'
# SimInput+=',krn15-k64-rnd64.aff-hybrid5'
# SimInput+=',krn16-k32-rnd64.aff-random'
# SimInput+=',krn16-k32-rnd64.aff-min-hops'
# SimInput+=',krn16-k32-rnd64.aff-hybrid5'
# SimInput+=',krn18-k8-rnd64.aff-random'
# SimInput+=',krn18-k8-rnd64.aff-min-hops'
# SimInput+=',krn18-k8-rnd64.aff-hybrid5'
# SimInput+=',krn19-k4-rnd64.aff-random'
# SimInput+=',krn19-k4-rnd64.aff-min-hops'
# SimInput+=',krn19-k4-rnd64.aff-hybrid5'
# SimInput+=',krn20-k2-rnd64.aff-random'
# SimInput+=',krn20-k2-rnd64.aff-min-hops'
# SimInput+=',krn20-k2-rnd64.aff-hybrid5'

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
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
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
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
    # all_sim+=$o8.fltsc-cmp-snuca-dist,
    all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug StreamEngine,StreamBase,LLCRubyStream,MLCRubyStream,StreamElement,ExecFunc 2>&1 | tee /benchmarks/core.log
        # --gem5-variant fast \
        # --perf-command \
        # --gem5-debug StreamLoopBound 2>&1 | tee /benchmarks/llc.log \
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 