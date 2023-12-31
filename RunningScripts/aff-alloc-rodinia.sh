#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
Benchmark+='rodinia.pathfinder-avx512-nounroll-random-skew1k,'
Benchmark+='rodinia.hotspot-avx512-fix-random-skew1,'
Benchmark+='rodinia.srad_v2-avx512-fix-random-skew1,'
Benchmark+='rodinia.hotspot3D-avx512-fix-fuse-random-skew1,'
# Benchmark+='rodinia.pathfinder-avx512-nounroll-random,'
# Benchmark+='rodinia.hotspot-avx512-fix-random,'
# Benchmark+='rodinia.srad_v2-avx512-fix-random,'
# Benchmark+='rodinia.hotspot3D-avx512-fix-fuse-random,'
# Benchmark+='rodinia.pathfinder-avx512-nounroll,'
# Benchmark+='rodinia.hotspot-avx512-fix,'
# Benchmark+='rodinia.srad_v2-avx512-fix,'
# Benchmark+='rodinia.hotspot3D-avx512-fix-fuse,'
SimInput=''
# SimInput+=',large'
# SimInput+=',large2x'
# SimInput+=',large4x'
# SimInput+=',large8x'
SimInput+=',large2x-cold'
SimInput+=',large4x-cold'
SimInput+=',large8x-cold'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
# RubyConfig=8x8c
RubyConfig=8x8m2x2
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

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
    # --transform-debug StaticStreamRegionAnalyzer,StaticMemStream 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8.fltsc-cmp-rmtcfg,
    all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug StreamEngine,ISAStreamEngine,StreamBase --gem5-debug-start 18800962000 2>&1 | tee /benchmarks/srad.log
        # --gem5-debug Stats 2>&1 | tee /benchmarks/llc.log
        # --perf-command \
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 