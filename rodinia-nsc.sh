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
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

RubyConfig=8x8c
Threads=64
Parallel=64

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d 

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    all_sim+=$o8.fltsc-cmp-snuca-rmtcfg,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --no-job-log \
        # --gem5-debug StreamEngine,ISAStreamEngine,StreamBase --gem5-debug-start 18800962000 2>&1 | tee /benchmarks/srad.log
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel 