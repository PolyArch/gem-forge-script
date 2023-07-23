#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gap.sssp_check,'
Benchmark+='gap.sssp,'
Benchmark+='gap.pr_pull_shuffle,'
Benchmark+='gap.pr_push,'
Benchmark+='gap.bfs_pull_shuffle_nobrk,'
Benchmark+='gap.bfs_push_check,'
Benchmark+='gap.bfs_push,'
SimInput=krn18-k16
# SimInput=krn18-k16-cold

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
Parallel=100
sim_replay_prefix=base/ruby/uno
i4=$sim_replay_prefix/i4.${RubyConfig}
o4=$sim_replay_prefix/o4.${RubyConfig}
o8=$sim_replay_prefix/o8.${RubyConfig}
# sim_replay=$i4,$o4,$o8
sim_replay=$i4,$o4,$o8,$i4.bingo-l2pf,$o4.bingo-l2pf,$o8.bingo-l2pf
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
    --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel