#!/bin/bash

# rm -f /tmp/job_scheduler.*

SimInputSize=pic
# All
Benchmark='-b spec.619.lbm_s'

SimTrace=''

# Before running this script, make sure:
# > cd where.spec2017.is
# > source shrc
# > export SPEC2017_SUITE_PATH=where.spec2017.is

# Build the byte code.
# python Driver.py $Benchmark --build

# Run the binary for a long time to get the profile.
python Driver.py $Benchmark --profile


# python Driver.py $Benchmark $SimTrace --trace

# python Driver.py $Benchmark $SimTrace -t valid.ex -d

# RubyConfig=8x8m4x4
RubyConfig=8x8t4x4
# RubyConfig=8x8c
Threads=1
Parallel=40
i4=replay/ruby/single/i4.tlb.$RubyConfig
o4=replay/ruby/single/o4.tlb.$RubyConfig
o8=replay/ruby/single/o8.tlb.$RubyConfig
sim_replay=$o8,$o8.bingo-l2pf
# sim_replay=$o8
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInputSize \
#     --sim-configs $sim_replay --input-threads $Threads -j $Parallel -s &

# StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp
StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d 
#     --transform-debug StaticStreamRegionAnalyzer 2>&1 | tee hhh.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=stream/ruby/single/i4.tlb.$rubyc.c
    local o4=stream/ruby/single/o4.tlb.$rubyc.c-gb-fifo
    local o8=stream/ruby/single/o8.tlb.$rubyc.c-gb-fifo
    # local all_sim=$o8,$o8.flts-mc
    local all_sim=$o8.fltsc-cmp
    # local all_sim=$o8.fltsc-memm-cmp-reuse-nuca-imc
    # local all_sim=$o8.fltsc-cmp-imc,$o8.fltsc-memm-cmp-reuse-nuca-imc
    # local all_sim=$o8.fltsc-cmp,$o8.fltsc-cmp-imc,$o8.fltsc-memm-cmp-reuse-nuca-imc
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input-size $input \
        --input-threads $threads \
        -s -j $parallel 
        # --gem5-debug O3CPU --gem5-debug-start 15700000000 --gem5-max-ticks 15800000000 | tee /benchmarks/rodinia.log 
        # --gem5-debug StreamFloatPolicy,StreamFloatController,StreamEngine,ISAStreamEngine --gem5-debug-start 3526088000 | tee /benchmarks/rodinia.rewind.log 
        # --gem5-debug LLCRubyStream,MLCRubyStream,RubyNetwork,RubyQueue --gem5-debug-start 10756089240 --gem5-max-ticks 10759120791 | tee hhh.log 
}
# run_ssp $StreamTransform $RubyConfig $SimInputSize $Threads $Parallel