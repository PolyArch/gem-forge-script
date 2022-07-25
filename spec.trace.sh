#!/bin/bash

# rm -f /tmp/job_scheduler.*

SimInputSize=test
# All
Benchmark='-b spec.619.lbm_s'

# Before running this script, make sure:
# > cd where.spec2017.is
# > source shrc
# > export SPEC2017_SUITE_PATH=where.spec2017.is

# Build the byte code.
# python Driver.py $Benchmark --build

# Run the binary for a long time to get the profile.
python Driver.py $Benchmark --profile

# Below are not tested yet.

SimTrace='--simpoint-mode=region'

# Build the simpoint.
# python Driver.py $Benchmark $SimTrace --simpoint

# Trace the simpoint.
# python Driver.py $Benchmark $SimTrace --trace

# Process the trace (do thing)
# python Driver.py $Benchmark $SimTrace -t replay -d

Threads=1
Parallel=40
o8=replay/o8
sim_replay=$o8
# python Driver.py $Benchmark $SimTrace -t replay --sim-input-size $SimInputSize \
#     --sim-configs $sim_replay --input-threads $Threads -j $Parallel -s 
