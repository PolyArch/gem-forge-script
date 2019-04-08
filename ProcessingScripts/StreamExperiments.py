
from BenchmarkDrivers.MultiProgramBenchmark import MultiProgramBenchmark

import Utils.Gem5Stats as Gem5Stats
import Utils.StreamMessage_pb2 as StreamMessage_pb2
import json

import os


class StreamExperiments(object):
    def __init__(self, driver):
        self.driver = driver
        self.stream_transform_config = self.driver.transform_manager.get_config(
            'stream')
        self.stream_simulation_configs = self.driver.simulation_manager.get_configs(
            'stream')

        mismatches = None
        n_single_benchmarks = 0
        for benchmark in self.driver.benchmarks:
            if not isinstance(benchmark, MultiProgramBenchmark):
                ret = self.analyzeStaticStreamForBenchmark(benchmark)
                n_single_benchmarks += 1
                if mismatches is None:
                    mismatches = ret
                else:
                    for i in range(len(mismatches)):
                        mismatches[i] += ret[i]
        for i in range(len(mismatches)):
            mismatches[i] /= n_single_benchmarks
            print('Average mismatch rate at level {level} is {mismatch}'.format(
                level=i,
                mismatch=mismatches[i]))

        self.replay_transform_config = self.driver.transform_manager.get_config(
            'replay')
        self.replay_simulation_configs = self.driver.simulation_manager.get_configs(
            'replay')

        self.single_program_speedup = dict()
        self.multi_program_speedup = dict()

        for benchmark in self.driver.benchmarks:
            if isinstance(benchmark, MultiProgramBenchmark):
                self.analyzeMultiProgramBenchmark(benchmark)
            else:
                speedup = self.analyzeSingleBenchmark(benchmark)

        for replay_simulation_config in self.replay_simulation_configs:
            for stream_simulation_config in self.stream_simulation_configs:
                single_geomean = self.geomean(
                    replay_simulation_config, stream_simulation_config,
                    self.single_program_speedup)
                multi_geomean = self.geomean(
                    replay_simulation_config, stream_simulation_config,
                    self.multi_program_speedup)
                print('geomean single {s} multi {m} diff {d}'.format(
                    s=single_geomean,
                    m=multi_geomean,
                    d=multi_geomean/single_geomean,
                ))

    def geomean(self, replay_simulation_config, stream_simulation_config, spd):
        all_speedup = [spd[b][replay_simulation_config]
                       [stream_simulation_config] for b in spd]
        if len(all_speedup) == 0:
            return 1.0
        prod = 1.0
        for x in all_speedup:
            prod *= x
        return prod ** (1./len(all_speedup))

    def get_single_program_time(self, benchmark, transform_config, simulation_config):
        time = 0.0
        for trace in benchmark.get_traces():
            result = self.driver.get_simulation_result(
                benchmark, trace, transform_config, simulation_config)
            time += result.stats.get_sim_seconds() * trace.weight
        return time

    def analyzeSingleBenchmark(self, benchmark):
        replay_time = dict()
        for replay_simulation_config in self.replay_simulation_configs:
            time = self.get_single_program_time(
                benchmark, self.replay_transform_config, replay_simulation_config)
            replay_time[replay_simulation_config] = time
        stream_time = dict()
        for stream_simulation_config in self.stream_simulation_configs:
            time = self.get_single_program_time(
                benchmark, self.stream_transform_config, stream_simulation_config)
            stream_time[stream_simulation_config] = time
        speedups = dict()
        for replay_simulation_config in replay_time:
            speedups[replay_simulation_config] = dict()
            for stream_simulation_config in stream_time:
                speedup = replay_time[replay_simulation_config] / \
                    stream_time[stream_simulation_config]
                speedups[replay_simulation_config][stream_simulation_config] = speedup
                print('{b} Speedup {stream}/{replay} is {speedup}.'.format(
                    b=benchmark.get_name(),
                    stream=stream_simulation_config.get_simulation_id(),
                    replay=replay_simulation_config.get_simulation_id(),
                    speedup=speedup
                ))
        self.single_program_speedup[benchmark] = speedups
        return speedups

    def getAllTimeForMultiProgramBenchmark(self,
                                           multi_program_benchmark, multi_program_tdgs, simulation_configs):

        benchmark_single_time = dict()
        benchmark_multi_time = dict()
        for benchmark in multi_program_benchmark.benchmarks:
            benchmark_single_time[benchmark] = dict()
            benchmark_multi_time[benchmark] = dict()
            for simulation_config in simulation_configs:
                benchmark_single_time[benchmark][simulation_config] = 0.0
                benchmark_multi_time[benchmark][simulation_config] = 0.0

        for t in multi_program_tdgs:
            multi_program_tdg = multi_program_benchmark.tdg_map[t]
            single_program_tdgs = multi_program_tdg.tdgs
            assert(len(single_program_tdgs) == len(
                multi_program_benchmark.benchmarks))

            # Load multi program time.
            for simulation_config in simulation_configs:
                multi_program_tdg_sim_dir = simulation_config.get_gem5_dir(t)
                multi_program_tdg_sim_stats = os.path.join(
                    multi_program_tdg_sim_dir, 'stats.txt')
                gem5Stats = Gem5Stats.Gem5Stats(
                    multi_program_benchmark, multi_program_tdg_sim_stats)
                for i in range(len(single_program_tdgs)):
                    benchmark = multi_program_benchmark.benchmarks[i]
                    time = gem5Stats['system.cpu{i}.numCycles'.format(i=i)]
                    benchmark_multi_time[benchmark][simulation_config] += time

            # Load single program time.
            for i in range(len(single_program_tdgs)):
                benchmark = multi_program_benchmark.benchmarks[i]
                single_program_tdg = single_program_tdgs[i]
                for simulation_config in simulation_configs:
                    single_program_tdg_sim_dir = simulation_config.get_gem5_dir(
                        single_program_tdg)
                    single_program_tdg_sim_stats = os.path.join(
                        single_program_tdg_sim_dir, 'stats.txt')
                    gem5Stats = Gem5Stats.Gem5Stats(
                        benchmark, single_program_tdg_sim_stats)
                    single_program_time = gem5Stats['system.cpu.numCycles']
                    benchmark_single_time[benchmark][simulation_config] += \
                        single_program_time
        return (benchmark_single_time, benchmark_multi_time)

    def speedupHack(self, rp_time, st_time, spd):
        for benchmark in rp_time:
            spd[benchmark] = dict()
            assert(benchmark in st_time)
            for rp_config in self.replay_simulation_configs:
                spd[benchmark][rp_config] = dict()
                assert(rp_config in rp_time[benchmark])
                for st_config in self.stream_simulation_configs:
                    assert(st_config in st_time[benchmark])
                    rp = rp_time[benchmark][rp_config]
                    st = st_time[benchmark][st_config]
                    spd[benchmark][rp_config][st_config] = rp / st

    def analyzeMultiProgramBenchmark(self, multi_program_benchmark):
        # First get all multi-program tdgs.
        replay_multi_program_tdgs = multi_program_benchmark.get_tdgs(
            self.replay_transform_config)
        rp_single, rp_multi = self.getAllTimeForMultiProgramBenchmark(
            multi_program_benchmark, replay_multi_program_tdgs, self.replay_simulation_configs)
        stream_multi_program_tdgs = multi_program_benchmark.get_tdgs(
            self.stream_transform_config)
        st_single, st_multi = self.getAllTimeForMultiProgramBenchmark(
            multi_program_benchmark, stream_multi_program_tdgs, self.stream_simulation_configs)
        # Compute speedup.
        self.speedupHack(rp_single, st_single, self.single_program_speedup)
        self.speedupHack(rp_multi, st_multi, self.multi_program_speedup)

        for rp_config in self.replay_simulation_configs:
            for st_config in self.stream_simulation_configs:
                for benchmark in multi_program_benchmark.benchmarks:
                    single = self.single_program_speedup[benchmark][rp_config][st_config]
                    multi = self.multi_program_speedup[benchmark][rp_config][st_config]
                    print('{b}, single {s}, multi {m}, diff {d}'.format(
                        b=benchmark.get_name(),
                        s=single,
                        m=multi,
                        d=multi/single,
                    ))

    def analyzeStaticStreamForBenchmark(self, benchmark):
        print('Start static stream analysis for {b}'.format(
            b=benchmark.get_name()))
        ssa = StaticStreamAnalyzer(benchmark, self.stream_transform_config)
        return ssa.mismatches


class StaticStreamAnalyzer(object):

    class RegionAnalyzer(object):
        def __init__(self, trace, fn):
            self.trace = trace
            self.streams = dict()
            self.analyze(fn)

        def analyze(self, fn):
            stream_region = StreamMessage_pb2.StreamRegion()
            f = open(fn)
            stream_region.ParseFromString(f.read())
            f.close()
            for s in stream_region.streams:
                stream_name = s.name.split()[3]
                if stream_name not in self.streams:
                    self.streams[stream_name] = [s]
                else:
                    inserted = False
                    for i in range(len(self.streams[stream_name])):
                        if self.streams[stream_name][i].config_loop_level > s.config_loop_level:
                            continue
                        self.streams[stream_name].insert(i, s)
                        inserted = True
                        break
                    if not inserted:
                        self.streams[stream_name].append(s)

        def get_mismatch_streams_at_level(self, level):
            mismatch_streams = list()
            for stream_name in self.streams:
                streams = self.streams[stream_name]
                if len(streams) <= level:
                    continue
                s = streams[level]
                if s.dynamic_info.is_qualified != s.static_info.is_qualified:
                    mismatch_streams.append(s)
            return mismatch_streams

        def get_total_qualified_mem_accesses(self):
            total = 0
            for stream_name in self.streams:
                s = self.streams[stream_name][0]
                if s.type == 'phi':
                    continue
                if not s.dynamic_info.is_qualified:
                    continue
                total += s.dynamic_info.total_accesses
            return total

        def get_total_loop_mem_accesses(self):
            total = 0
            for stream_name in self.streams:
                s = self.streams[stream_name][0]
                if s.type == 'phi':
                    continue
                total += s.dynamic_info.total_accesses
            return total

    class TraceAnalyzer(object):
        def __init__(self, parent, trace):
            self.parent = parent
            self.trace = trace
            self.regions = list()
            self.analyze()
            self.total_qualified_accesses = float(sum(
                [r.get_total_qualified_mem_accesses() for r in self.regions]))
            self.total_loop_accesses = float(sum(
                [r.get_total_loop_mem_accesses() for r in self.regions]))

        def analyze(self):
            tdg_extra_path = self.parent.benchmark.get_tdg_extra_path(
                self.parent.stream_transform_config, self.trace)
            for item in os.listdir(tdg_extra_path):
                if not os.path.isdir(os.path.join(tdg_extra_path, item)):
                    continue
                stream_region_path = os.path.join(
                    tdg_extra_path, item, 'streams.info')
                self.regions.append(StaticStreamAnalyzer.RegionAnalyzer(
                    self.trace, stream_region_path))

        def analyze_mismatch_at_level(self, level):
            total_mismatch_mem_accesses = 0
            for r in self.regions:
                mismatch_streams = r.get_mismatch_streams_at_level(level)
                for s in mismatch_streams:
                    dynamic_info = s.dynamic_info
                    static_info = s.static_info
                    if dynamic_info.is_aliased:
                        # Ignore the mismatch due to aliasing.
                        continue
                    if dynamic_info.total_accesses == 0:
                        # Ignore the mismatch due to no accesses in the trace.
                        continue
                    if not dynamic_info.is_qualified:
                        # Ingore the case where static reports stream but dynamic doesn't
                        continue
                    self.print_mismatch(s)
                    if s.type != 'phi':
                        total_mismatch_mem_accesses += dynamic_info.total_accesses
            if self.total_qualified_accesses != 0:
                total_mismatch_mem_accesses /= self.total_qualified_accesses
            return total_mismatch_mem_accesses

        def print_mismatch(self, s):
            print('Mismatch stream! weight {weight:.2f} lv {lv:1} dynamic {dynamic:1} static {static:1} reason {reason:20}: {s}'.format(
                weight=(s.dynamic_info.total_accesses /
                        self.total_qualified_accesses *
                        self.trace.get_weight()) if self.total_qualified_accesses != 0 else 0.0,
                lv=s.loop_level - s.config_loop_level,
                dynamic=s.dynamic_info.is_qualified,
                static=s.static_info.is_qualified,
                reason=StreamMessage_pb2.StaticStreamInfo.StaticNotStreamReason.Name(
                    s.static_info.not_stream_reason),
                s=s.name
            ))

    def __init__(self, benchmark, stream_transform_config):
        self.benchmark = benchmark
        self.stream_transform_config = stream_transform_config
        self.analyze()

    def analyze(self):
        self.traces = list()
        self.mismatches = list()
        for trace in self.benchmark.get_traces():
            self.traces.append(StaticStreamAnalyzer.TraceAnalyzer(self, trace))
        for level in xrange(1):
            total_mismatch_mem_accesses = 0.0
            for trace in self.traces:
                trace_mismatch_mem_accesses = trace.analyze_mismatch_at_level(
                    level)
                total_mismatch_mem_accesses += trace_mismatch_mem_accesses * trace.trace.get_weight()
            print('========= Analyzing Loop Level {level} Mismatch MemAccesses {weight:.3f}'.format(
                level=level, weight=total_mismatch_mem_accesses))
            self.mismatches.append(total_mismatch_mem_accesses)


def analyze(driver):
    StreamExperiments(driver)
