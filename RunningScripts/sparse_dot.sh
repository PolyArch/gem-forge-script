#!bash

# rm -f /tmp/job_scheduler.*

# Specify the benchmark. The source file is in
# transform/benchmark/GemForgeMicroSuite/stream/vec_add/omp_vec_add_avx
Benchmark='-b '
Benchmark+='gfm.sparse_dot_prod,'
# Benchmark+='gfm.dot_prod_avx,'

# Specify the input size. Check driver/BenchmarkDrivers/GemForgeMicroSuite.py
# for the details of how the benchmark is built and simulated.
SimInput=large-cold

# Specify the number of threads. The workload is parallelized with OpenMP.
Threads=64

# The following two commands build the LLVM bytecode of the workload in
# /gem-forge-stack/result/stream/gfm/omp_vec_add_avx
# You can check the IR in raw.ll (text format).
SimTrace='--fake-trace'
# python Driver.py $Benchmark --build
# python Driver.py $Benchmark $SimTrace --trace

# This command takes the LLVM bytecode and build the baseline binary.
# Baseline means there is no stream specialization.
# The transformed binary is located in:
# /gem-forge-stack/result/stream/gfm/omp_vec_add_avx/valid.ex/fake.0.tdg.extra
BaseTrans=valid.ex
# python Driver.py $Benchmark $SimTrace -t $BaseTrans -d

RubyConfig=8x8c
Parallel=100

# Simulate the baseline binary with gem5 O3 core.
# Notice that the simulation configuration is defined in:
# driver/Configurations/Simulation/base/ruby/uno/...
# Configurations are json files that gets processed by
# driver/Utils/Gem5ConfigureManager.py
#
# Simulation results are in:
# /gem-forge-stack/result/stream/gfm/omp_vec_add_avx/valid.ex/base.ruby.uno.o8.8x8c-l256-s64B-ch64B.bingo-l2pf16/fake.0.tdg.large.thread64
#
# For example, to check the cycles, check system.future_cpus0.numCycles
# in the stats.txt
# I also have a script to help summarize some stats:
# python /gem-forge-stack/driver/ProcessingScripts/SSPExRubyExperiments.py stats.txt
sim_replay_prefix=base/ruby/uno
o8=$sim_replay_prefix/o8.${RubyConfig}
sim_replay=$o8.bingo-l2pf
# python Driver.py $Benchmark $SimTrace -t valid.ex --sim-input-size $SimInput \
#     --sim-configs $sim_replay --input-threads $Threads -s -j $Parallel \
#     --no-job-log \
    # --gem5-debug Quiesce,SyscallVerbose | tee gfm.log

# Similarly, this command build the stream specialized binary.
# The binary is in:
# /gem-forge-stack/result/stream/gfm/omp_vec_add_avx/stream.ex.static.so.store.cmp-bnd-elim-nst/ss.ruby.uno.o8.8x8c-l256-s1kB-ch4kB.f2048-c-gb.fltsc-cmp/fake.0.tdg.large.thread64
StreamTransform=stream/ex/static/so.store
# StreamTransform=stream/ex/static/so.store.cmp-bnd-elim-nst
# python Driver.py $Benchmark $SimTrace -t $StreamTransform -d \
#     --transform-debug StaticStreamRegionAnalyzer,StaticIndVarStream,StaticStream
    
    # ,StaticStream,StaticIndVarStream,StaticMemStream,StreamExecutionTransformer

run_ssp () {
    local trans=$1
    local rubyc=$2
    local input=$3
    local threads=$4
    local parallel=$5
    local o8=ss/ruby/uno/o8.$rubyc.c-gb-fifo
    local all_sim=''
    all_sim+=$o8,
    python Driver.py $Benchmark $SimTrace -t $trans \
        --sim-configs $all_sim \
        --sim-input $input \
        --input-threads $threads \
        -s -j $parallel \
        --no-job-log \
        # --gem5-debug ISAStreamEngine,StreamEngine,StreamBase | tee /benchmarks/gfm-new.log
        # --gem5-debug MLCStreamPUM 2>&1 | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM,MLCRubyStream | tee /benchmarks/gfm-new.log
        # --gem5-debug StreamNUCAManager,MLCStreamPUM | tee /benchmarks/gfm-new.log
        # --gem5-debug LLCRubyStream,MLCRubyStream --gem5-debug-start 4228029500 | tee /benchmarks/gfm-new.log
}

# Also, this command will run the stream binary with gem5.
# Comparing the numCycles, it should be much faster than the
# baseline version.
run_ssp $StreamTransform $RubyConfig $SimInput $Threads $Parallel