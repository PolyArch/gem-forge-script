#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gfm.omp_acc_gen_mm_ss_avx,'
# Benchmark+='gfm.omp_acc_gen_mm_reg_M2048_N2048_K64_avx,'
# Benchmark+='gfm.omp_acc_gen_mm_reg_pack_M2048_N2048_K64_avx,'
# Benchmark+='gfm.omp_acc_gen_mm_M2048_N2048_K2048_amx,'
# Benchmark+='gfm.omp_acc_gen_mm_pack_M2048_N2048_K2048_amx,'
# Benchmark+='gfm.omp_acc_gen_mm_pack_2_M2048_N2048_K2048_amx,'
# Benchmark+='gfm.omp_acc_gen_mm_pack_4_M2048_N2048_K2048_amx,'
Benchmark+='gfm.omp_acc_gen_mm_bypass_M2048_N2048_K2048_amx,'
SimInput=''
# SimInput+='large,'
SimInput+='large-cold'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

# RubyConfig=8x8c
RubyConfig=8x8m4x4
Threads=64
Parallel=100

StreamTransform=''
# StreamTransform+='stream/ex/static/so,'
# StreamTransform+='stream/ex/static/so.store,'
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
    # --transform-debug StreamExecutionTransformer 2>&1 | tee /benchmarks/shit.log

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local i4=ss/ruby/uno/i4.$rubyc.c-gb-fifo
    local o4=ss/ruby/uno/o4.$rubyc.c-gb-fifo
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local o8_zen2=ss/ruby/uno/o8.cache-32kB-512kB-4MB.${rubyc}.c-gb-fifo
    local o8_sapphire_rapids=ss/ruby/uno/o8-sapphire-rapids.${rubyc}.c-gb-fifo
    local all_sim=''
    # all_sim+=$o8,
    # all_sim+=$o8.idea-seq,
    # all_sim+=$o8_zen2,
    # all_sim+=$o8_zen2.l2stride,
    # all_sim+=$o8_sapphire_rapids.idea-seq,
    all_sim+=$o8_sapphire_rapids.l2stride,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        --gem5-variant fast \
        # --no-job-log \
        # --gem5-debug ProtocolTrace,RubyCache,L0RubyStreamBase --gem5-debug-start 1252846000 --gem5-max-ticks 1352846000 2>&1 | tee /benchmarks/cmp.log
        # --perf-command \
        # --gem5-debug ISAStreamEngine,StreamEngine,StreamBase,LLCRubyStream,MLCRubyStream | tee /benchmarks/cmp-cache.log
}
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel