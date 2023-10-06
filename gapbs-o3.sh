#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='gap.sssp_sf_delta1,'
Benchmark+='gap.pr_pull,'
Benchmark+='gap.pr_push,'
Benchmark+='gap.bfs_push_check,'
Benchmark+='gap.bfs_pull,'
Benchmark+='gap.bfs_pull_nobrk,'
Benchmark+='gap.bfs,'
SimInput=''
SimInput+=',krn10-k4'


SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Threads=64
Parallel=64
sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=$o8,$o8.bingo-l2pf
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
    --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel
