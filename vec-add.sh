#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gfm.omp_vec_add_avx,'
SimInput=large
Threads=64

SimTrace='--fake-trace'
python Driver.py $Benchmark --build
python Driver.py $Benchmark $SimTrace --trace

BaseTrans=valid.ex
python Driver.py $Benchmark $SimTrace -t $BaseTrans -d
RubyConfig=8x8c
Parallel=100
sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=$o8.bingo-l2pf
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
--sim-configs $sim_replay --input-threads $Threads -s -j $Parallel \
    # --gem5-debug Quiesce,SyscallVerbose | tee gfm.log

StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StreamLoopEliminator

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    all_sim+=$o8.fltsc-cmp,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        # --gem5-debug MLCStreamPUM 2>&1 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM,MLCRubyStream | tee /benchmarks/gfm-new.log
        # --gem5-debug ISAStreamEngine,StreamEngine --gem5-debug-start 16936500 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM | tee /benchmarks/gfm-new.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 4228029500 | tee /benchmarks/gfm-new.log
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel
