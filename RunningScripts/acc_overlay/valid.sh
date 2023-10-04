#!/bin/bash

# rm -f /tmp/job_scheduler.*

Benchmark='-b '
# Benchmark+='gfm.omp_acc_gen_mm_avx,'
# Benchmark+='gfm.omp_acc_gen_mm_M2048_N2048_K64_avx,'
# Benchmark+='gfm.omp_acc_gen_mm_reg_M2048_N2048_K64_avx,'
# Benchmark+='gfm.omp_mm_aocl,'
# Benchmark+='gfm.omp_acc_gen_mm_M2048_N2048_K2048_amx,'
Benchmark+='gfm.omp_acc_gen_mm_pack_M2048_N2048_K2048_amx,'
SimInput=''
SimInput+='large,'
# SimInput+='large-cold'
# SimInput+='MNK.512.512.512'
# SimInput+='MNK-cold.512.512.512'

SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

RubyConfig=8x8c
Threads=1
Parallel=50

BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d

sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
o8_zen2=$sim_replay_prefix/o8.cache-32kB-512kB-4MB.${RubyConfig}
sim_replay=''
# sim_replay+=$o8,
# sim_replay+=$o8.bingo-l2pf,
sim_replay+=$o8.idea-seq,
# sim_replay+=$o8.huge-l1,
# sim_replay+=$o8.huge-l1.bingo,
# sim_replay+=$o8.huge-l1.stride,
# sim_replay+=$o8.huge-l2,
# sim_replay+=$o8.huge-l2.stride,
# sim_replay+=$o8.huge-l2.stride-l2stride,
# sim_replay+=$o8.stride,
# sim_replay+=$o8.stride-l2stride,
# sim_replay+=$o8_zen2.stride,
# sim_replay+=$o8_zen2.stride-l2stride,
python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
    --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel \
    --gem5-variant fast \
    --no-job-log \
    # --gem5-debug ProtocolTrace,RubyPrefetcher --gem5-debug-start 2300000000 --gem5-max-ticks 2400000000 2>&1 | tee /benchmarks/mm.log
    # --gem5-debug O3PipeView --gem5-debug-start 1200000000 --gem5-max-ticks 1201000000 --gem5-debug-file mm.out