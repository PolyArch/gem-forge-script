#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='rodinia.pathfinder-avx512-nounroll,'
Benchmark+='rodinia.hotspot-avx512-fix,'
Benchmark+='rodinia.srad_v2-avx512-fix,'
Benchmark+='rodinia.hotspot3D-avx512-fix-fuse,'
Benchmark+='rodinia.streamcluster,'
SimInput=''
SimInput+=',large'

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