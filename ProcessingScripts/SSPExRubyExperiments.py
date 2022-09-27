"""
Simple process script to process stats for multi-core configurations.
"""

import re

import os
import sys
script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

import PUMJitterExperiments

__print_traffic__ = False

class TileStats(object):
    def __init__(self, tile_id):
        self.tile_id = tile_id
        self.load_blocked_cpi = 0
        self.load_blocked_ratio = 0
        self.l1d_access = 0
        self.l1d_misses = 0
        self.l2_access = 0
        self.l2_misses = 0
        self.l3_access = 0
        self.l3_misses = 0
        self.control_flits = 0
        self.data_flits = 0
        self.stream_flits = 0
        self.control_hops = 0
        self.data_hops = 0
        self.stream_hops = 0
        self.l3_transitions = dict()
        pass


class TileStatsParser(object):
    def __init__(self, tile_stats):
        self.tile_stats = tile_stats
        self.re = {
            'sim_ticks': self.format_re('sim_ticks'),
            'num_cycles': self.format_re(
                'system.future_cpus{tile_id}.numCycles'),
            'num_dyn_ops': self.format_re(
                'system.future_cpus{tile_id}.committedOps'),
            'num_dyn_insts': self.format_re(
                'system.future_cpus{tile_id}.committedInsts'),
            'load_blocked_cpi': self.format_re(
                'system.future_cpus{tile_id}.loadBlockedCPI'),
            'load_blocked_ratio': self.format_re(
                'system.future_cpus{tile_id}.loadBlockedCyclesPercen*'),
            'l1d_access': self.format_re(
                'system.ruby.l0_cntrl{tile_id}.Dcache.demand_accesses'),
            'l1d_misses': self.format_re(
                'system.ruby.l0_cntrl{tile_id}.Dcache.demand_misses'),
            'l2_access': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.demand_accesses'),
            'l2_misses': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.demand_misses'),
            'l2_evicts': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated'),
            'l2_evicts_noreuse': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated_no_reuse'),
            'l2_evicts_noreuse_stream': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated_no_reuse_stream'),
            'l2_evicts_noreuse_ctrl_pkts': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated_no_reuse_noc_ctrl_msg'),
            'l2_evicts_noreuse_ctrl_evict_pkts': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated_no_reuse_noc_ctrl_evict_msg'),
            'l2_evicts_noreuse_data_pkts': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.cache.deallocated_no_reuse_noc_data_msg'),
            'l3_access': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.L2cache.demand_accesses'),
            'l3_misses': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.L2cache.demand_misses'),
            'l1tlb_access': self.format_re(
                'system.future_cpus{tile_id}.dtb.l1Accesses'),
            'l1tlb_misses': self.format_re(
                'system.future_cpus{tile_id}.dtb.l1Misses'),
            'l2tlb_access': self.format_re(
                'system.future_cpus{tile_id}.dtb.l2Accesses'),
            'l2tlb_misses': self.format_re(
                'system.future_cpus{tile_id}.dtb.l2Misses'),
            'noc_flit': ['system.ruby.network.flits_injected::total'],
            'noc_packet': ['system.ruby.network.packets_injected::total'],
            'avg_flit_network_lat': ['system.ruby.network.average_flit_network_latency'],
            'avg_flit_queue_lat': ['system.ruby.network.average_flit_queueing_latency'],
            'avg_sequencer_miss_lat': ['system.ruby.miss_latency_hist_seqr::mean'],
            'avg_sequencer_hit_lat': ['system.ruby.hit_latency_hist_seqr::mean'],
            'total_hops': ['system.ruby.network.total_hops'],
            'crossbar_act': self.format_re(
                'system.ruby.network.routers{tile_id}.crossbar_activity'),
            'commit_op': self.format_re(
                'system.future_cpus{tile_id}.committedOps'),
            'commit_inst': self.format_re(
                'system.future_cpus{tile_id}.committedInsts'),
            'idea_cycles': self.format_re(
                'system.future_cpus{tile_id}.ideaCycles$'),
            'idea_cycles_no_fu': self.format_re(
                'system.future_cpus{tile_id}.ideaCyclesNoFUTiming'),
            'idea_cycles_no_ld': self.format_re(
                'system.future_cpus{tile_id}.ideaCyclesNoLDTiming'),
            'allocated_elements': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numElementsAllocated'),
            'used_load_elements': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numLoadElementsUsed'),
            'stepped_load_elements': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numLoadElementsStepped'),
            'stepped_store_elements': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numStoreElementsStepped'),
            'num_floated': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numFloated'),
            'llc_sent_slice': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numLLCSentSlice'),
            'llc_migrated': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numLLCMigrated'),
            'mlc_response': self.format_re(
                'system.future_cpus{tile_id}.accelManager.se.numMLCResponse'),
            'dcache_core_requests': self.format_re(
                'system.ruby.l0_cntrl{tile_id}.coreRequests'),
            'dcache_core_stream_requests': self.format_re(
                'system.ruby.l0_cntrl{tile_id}.coreStreamRequests'),
            'llc_core_requests': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.coreRequests'),
            'llc_core_stream_requests': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.coreStreamRequests'),
            'llc_llc_stream_requests': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamRequests'),
            'llc_llc_ind_stream_requests': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcIndStreamRequests'),
            'llc_llc_multicast_stream_requests': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcMulticastStreamRequests'),
            'llc_stream_computations': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamComputation'),
            'llc_stream_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsPerformed'),
            'llc_stream_committed_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsCommitted'),
            'llc_stream_locked_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsLocked'),
            'llc_stream_unlocked_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsUnlocked'),
            'llc_stream_line_conflict_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsLineConflict'),
            'llc_stream_xaw_conflict_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsXAWConflict'),
            'llc_stream_real_conflict_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsRealConflict'),
            'llc_stream_real_xaw_conflict_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsRealXAWConflict'),
            'llc_stream_deadlock_atomics': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcStreamAtomicsDeadlock'),
            'stream_wait_cycles': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numLoadElementWaitCycles'),
            'stream_data_traffic_fix': self.format_re(
                'system.cpu{tile_id}.accelManager.se.dataAccFix.hops'),
            'stream_data_traffic_cached': self.format_re(
                'system.cpu{tile_id}.accelManager.se.dataAccFix.cachedHops'),
            'stream_data_traffic_float': self.format_re(
                'system.cpu{tile_id}.accelManager.se.dataAccFloat.hops'),
            'core_data_traffic_fix': self.format_re(
                'system.future_cpus{tile_id}.statCoreDataHops'),
            'core_data_traffic_fix_ignored': self.format_re(
                'system.future_cpus{tile_id}.statCoreDataHopsIgnored'),
            'core_data_traffic_cached': self.format_re(
                'system.future_cpus{tile_id}.statCoreCachedDataHops'),
            'core_data_traffic_cached_ignored': self.format_re(
                'system.future_cpus{tile_id}.statCoreCachedDataHopsIgnored'),
            'core_committed_microops': self.format_re(
                'system.future_cpus{tile_id}.statCoreCommitMicroOps'),
            'core_committed_microops_ignored': self.format_re(
                'system.future_cpus{tile_id}.statCoreCommitMicroOpsIgnored'),
            'core_committed_microops_gem_forge': self.format_re(
                'system.future_cpus{tile_id}.statCoreCommitMicroOpsGemForge'),
            'core_se_microops': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedComputeMicroOps'),
            'core_se_microops_atomic': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedAtomicComputeMicroOps'),
            'core_se_microops_load': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedLoadComputeMicroOps'),
            'core_se_microops_store': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedStoreComputeMicroOps'),
            'core_se_microops_reduce': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedReduceMicroOps'),
            'core_se_microops_update': self.format_re(
                'system.cpu{tile_id}.accelManager.se.numCompletedUpdateMicroOps'),
            'llc_se_microops': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamComputeMicroOps'),
            'llc_se_microops_atomic': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamAtomicComputeMicroOps'),
            'llc_se_microops_load': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamLoadComputeMicroOps'),
            'llc_se_microops_store': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamStoreComputeMicroOps'),
            'llc_se_microops_reduce': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamReduceMicroOps'),
            'llc_se_microops_update': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.llcScheduledStreamUpdateMicroOps'),
            'mem_bytes_read': self.format_re(
                'system.mem_ctrls{tile_id}.bytes_read::total'),
            'mem_num_reads': self.format_re(
                'system.mem_ctrls{tile_id}.num_reads::total'),
            'mem_bw_read': self.format_re(
                'system.mem_ctrls{tile_id}.bw_read::total'),
            'mem_bytes_write': self.format_re(
                'system.mem_ctrls{tile_id}.bytes_written::total'),
            'mem_num_writes': self.format_re(
                'system.mem_ctrls{tile_id}.num_writes::total'),
            'mem_bw_write': self.format_re(
                'system.mem_ctrls{tile_id}.bw_write::total'),
            'mem_bw_total': self.format_re(
                'system.mem_ctrls{tile_id}.bw_total::total'),
            'pum_total_cycle': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.pumTotalCycles'),
            'pum_prefetch_cycle': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.pumPrefetchCycles'),
            'pum_compile_cycle': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.pumCompileCycles'),
            'pum_reduce_cycle': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.pumReduceCycles'),
            'pum_mix_cycle': self.format_re(
                'system.ruby.l1_cntrl{tile_id}.pumMixCycles'),
            'pum_compute_cycle': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.pumComputeCycles'),
            'pum_move_cycle': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.pumDataMoveCycles'),
            'pum_compute_cmds': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.pumComputeCmds'),
            'pum_compute_ops': self.format_re(
                'system.ruby.l2_cntrl{tile_id}.pumComputeOps'),
        }
        for addr in ['Affine', 'Indirect', 'PointerChase', 'MultiAffine']:
            for cmp in ['LoadCompute', 'StoreCompute', 'AtomicCompute', 'Update', 'Reduce']:
                core_microops = f'core_se_microps_{addr}_{cmp}'
                core_stats = f'numCompleted{addr}{cmp}MicroOps'
                self.re[core_microops] = self.format_re(
                    'system.cpu{tile_id}.accelManager.se.' + core_stats)
                llc_microops = f'llc_se_microps_{addr}_{cmp}'
                llc_stats = f'llcScheduledStream{addr}{cmp}MicroOps'
                self.re[llc_microops] = self.format_re(
                    'system.ruby.l2_cntrl{tile_id}.' + llc_stats)
        self.l2_transition_re = re.compile('system\.ruby\.L2Cache_Controller\.[A-Z_]+\.[A-Z0-9_]+::total')

    def format_re(self, expression):
        # Return two possible cases.
        return [
            expression.format(tile_id='{x}'.format(x=self.tile_stats.tile_id)),
            expression.format(tile_id='0{x}'.format(x=self.tile_stats.tile_id)),
        ]

    def parse(self, fields):
        if len(fields) < 2:
            return
        for k in self.re:
            for s in self.re[k]:
                if fields[0] == s:
                    self.tile_stats.__dict__[k] = float(fields[1])
                    break
        if fields[0] == 'system.ruby.network.flit_types_injected':
            ctrl, data, strm = self.parse_flit_type_breakdown(fields)
            self.tile_stats.control_flits += ctrl
            self.tile_stats.data_flits += data
            self.tile_stats.stream_flits += strm
        if fields[0] == 'system.ruby.network.total_hop_types':
            ctrl, data, strm = self.parse_flit_type_breakdown(fields)
            self.tile_stats.control_hops += ctrl
            self.tile_stats.data_hops += data
            self.tile_stats.stream_hops += strm
        self.parse_l2_stream_transition(fields)

    def parse_flit_type_breakdown(self, fields):
        # ! Keep this sync with CoherenceRequestType/CoherenceResponseType
        msg_type_req_category = [
            ('ctrl', 'Request::GETX'),
            ('ctrl', 'Request::UPGRADE'),
            ('ctrl', 'Request::GETS'),
            ('ctrl', 'Request::GETU'),
            ('ctrl', 'Request::GETH'),
            ('ctrl', 'Request::GET_INSTR'),
            ('ctrl', 'Request::INV'),
            ('ctrl', 'Request::INV_GET'),
            ('data', 'Request::PUTX'),
            ('ctrl', 'Request::WB_ACK'),
            ('ctrl', 'Request::DMA_READ'),
            ('data', 'Request::DMA_WRITE'),
            ('strm', 'Request::STREAM_CONFIG'),
            ('strm', 'Request::STREAM_FLOW'),
            ('strm', 'Request::STREAM_END'),
            ('ctrl', 'Request::STREAM_STORE'),
            ('strm', 'Request::STREAM_UNLOCK'),
            ('strm', 'Request::STREAM_MIGRATE'),
            ('data', 'Request::STREAM_FORWARD'),
            ('strm', 'Request::STREAM_COMMIT'),
            ('strm', 'Request::STREAM_NDC'),
            ('strm', 'Request::STREAM_PUM_DATA'),
        ]
        msg_type_resp_category = [
            ('ctrl', 'Response::MEMORY_ACK'),
            ('data', 'Response::DATA'),
            ('data', 'Response::DATA_EXCLUSIVE'),
            ('data', 'Response::MEMORY_DATA'),
            ('ctrl', 'Response::ACK'),
            ('ctrl', 'Response::WB_ACK'),
            ('ctrl', 'Response::UNBLOCK'),
            ('ctrl', 'Response::EXCLUSIVE_UNBLOCK'),
            ('ctrl', 'Response::INV'),
            ('strm', 'Response::STREAM_ACK'),
            ('strm', 'Response::STREAM_RANGE'),
            ('strm', 'Response::STREAM_DONE'),
            ('strm', 'Response::STREAM_NDC'),
        ]
        n_categories = 2
        n_types_per_category = 40
        n_types = n_categories * n_types_per_category
        flits = [float(fields[i * 4 + 2]) for i in range(n_types)]
        control_flits = 0
        data_flits = 0
        stream_flits = 0
        for i in range(n_types):
            category = i // n_types_per_category
            type_in_category = i % n_types_per_category
            msg_type_category = msg_type_req_category if category == 0 else msg_type_resp_category
            if type_in_category >= len(msg_type_category):
                continue
            msg_type, msg_name = msg_type_category[type_in_category]
            if __print_traffic__ and self.tile_stats.tile_id == 0:
                print(f'{msg_name} {flits[i]}')
            if msg_type == 'ctrl':
                control_flits += flits[i]
            elif msg_type == 'data':
                # print(f'DataTraffic of {msg_name} {flits[i]}')
                data_flits += flits[i]
            elif msg_type == 'strm':
                stream_flits += flits[i]
        return (control_flits, data_flits, stream_flits)

    def parse_l2_stream_transition(self, fields):
        match_obj = self.l2_transition_re.match(fields[0])
        if match_obj:
            vs = fields[0].split('.')
            state = vs[3]
            event = vs[4][:-7]
            if state not in self.tile_stats.l3_transitions:
                self.tile_stats.l3_transitions[state] = dict()
            self.tile_stats.l3_transitions[state][event] = float(fields[1])

def findTileIdForPrefix(x, prefix):
    if x.startswith(prefix):
        idx = x.find('.', len(prefix))
        if idx != -1:
            return int(x[len(prefix):idx])
    return -1

def findTileId(x):
    prefix = [
        'system.future_cpus',
        'system.ruby.l0_cntrl',
        'system.ruby.l1_cntrl',
        'system.ruby.l2_cntrl',
    ]
    for p in prefix:
        tileId = findTileIdForPrefix(x, p)
        if tileId != -1:
            return tileId
    return -1

def process(f):
    tile_stats = [TileStats(i) for i in range(64)]
    tile_stats_parser = [TileStatsParser(ts) for ts in tile_stats]
    for line in f:
        if line.find('End Simulation Statistics') != -1:
            break
        fields = line.split()
        if not fields:
            continue
        tile_id = findTileId(fields[0])
        if tile_id != -1:
            tile_stats_parser[tile_id].parse(fields)
            continue
        for p in tile_stats_parser:
            p.parse(fields)
    return tile_stats

def print_if_non_zero(v, f):
    if v > 0:
        print(f.format(v=v))

def print_stats(tile_stats):
    ticks_per_cycle = 500
    ticks_per_us = 1000000
    def sum_or_nan(vs):
        s = sum(vs)
        if s == 0:
            return float('NaN')
        return s

    def value_or_nan(x, v):
        return x.__dict__[v] if hasattr(x, v) else float('NaN')

    def value_or_zero(x, v):
        if isinstance(x, dict):
            return x[v] if v in x else 0.0
        return x.__dict__[v] if hasattr(x, v) else 0.0

    print('total l3 accesses       {v}'.format(
        v=sum_or_nan(ts.l3_access for ts in tile_stats)
    ))
    print('total l3 miss rate      {v}'.format(
        v=sum(ts.l3_misses for ts in tile_stats) /
        sum_or_nan(ts.l3_access for ts in tile_stats)
    ))
    print('total l2 miss rate      {v}'.format(
        v=sum(ts.l2_misses for ts in tile_stats) /
        sum_or_nan(ts.l2_access for ts in tile_stats)
    ))
    print('total l1d miss rate     {v}'.format(
        v=sum(ts.l1d_misses for ts in tile_stats) /
        sum_or_nan(ts.l1d_access for ts in tile_stats)
    ))
    # print('l2tlb miss / tlb access {v}'.format(
    #     v=sum_or_nan(value_or_nan(ts, 'l2tlb_misses') for ts in tile_stats) /
    #     sum_or_nan(value_or_nan(ts, 'l1tlb_access') for ts in tile_stats)
    # ))
    # print('l2tlb miss / l2 access  {v}'.format(
    #     v=sum_or_nan(value_or_nan(ts, 'l2tlb_misses') for ts in tile_stats) /
    #     sum_or_nan(value_or_nan(ts, 'l2tlb_access') for ts in tile_stats)
    # ))
    # print('l1tlb miss / tlb access {v}'.format(
    #     v=sum_or_nan(value_or_nan(ts, 'l1tlb_misses') for ts in tile_stats) /
    #     sum_or_nan(value_or_nan(ts, 'l1tlb_access') for ts in tile_stats)
    # ))
    print('total l2 evicts         {v}'.format(
        v=sum_or_nan(value_or_nan(ts, 'l2_evicts') for ts in tile_stats)
    ))
    # print('load blocked cpi        {v}'.format(
    #     v=sum(ts.load_blocked_cpi for ts in tile_stats) /
    #     len(tile_stats)
    # ))
    # print('load blocked percentage {v}'.format(
    #     v=sum(ts.load_blocked_ratio for ts in tile_stats) /
    #     len(tile_stats)
    # ))
    main_ts = tile_stats[0]
    print('total hops              {v}'.format(
        v=value_or_nan(main_ts, 'total_hops')
    ))
    print('noc flits               {v}'.format(
        v=value_or_nan(main_ts, 'noc_flit')
    ))
    print('noc packets             {v}'.format(
        v=value_or_nan(main_ts, 'noc_packet')
    ))
    print('control hops            {v}'.format(
        v=value_or_nan(main_ts, 'control_hops')
    ))
    print('data hops               {v}'.format(
        v=value_or_nan(main_ts, 'data_hops')
    ))
    print('stream hops             {v}'.format(
        v=value_or_nan(main_ts, 'stream_hops')
    ))
    print('crossbar activity       {v}'.format(
        v=sum(value_or_nan(ts, 'crossbar_act') for ts in tile_stats)
    ))
    print('crossbar / cycle        {v}'.format(
        v=sum(value_or_nan(ts, 'crossbar_act') for ts in tile_stats) / \
            (len(tile_stats) * main_ts.sim_ticks * ticks_per_cycle)
    ))
    print('main cpu cycles         {v}'.format(
        v=main_ts.sim_ticks / ticks_per_cycle
    ))
    print('main cpu opc            {v}'.format(
        v=main_ts.commit_op / main_ts.sim_ticks  * ticks_per_cycle
    ))
    # print('main cpu idea opc       {v}'.format(
    #     v=main_ts.commit_op / main_ts.idea_cycles if hasattr(main_ts, 'idea_cycles') else 0
    # ))
    # print('main cpu idea opc no ld {v}'.format(
    #     v=main_ts.commit_op / main_ts.idea_cycles_no_ld if hasattr(main_ts, 'idea_cycles_no_ld') else 0
    # ))
    # print('main cpu idea opc no fu {v}'.format(
    #     v=main_ts.commit_op / main_ts.idea_cycles_no_fu if hasattr(main_ts, 'idea_cycles_no_fu') else 0
    # ))
    # print('main load blocked cpi   {v}'.format(
    #     v=main_ts.load_blocked_cpi
    # ))
    # print('main blocked percentage {v}'.format(
    #     v=main_ts.load_blocked_ratio
    # ))
    print('num elements allocated  {v}'.format(
        v=sum(value_or_zero(ts, 'allocated_elements') for ts in tile_stats)
    ))
    print('num ld elements used    {v}'.format(
        v=sum(value_or_zero(ts, 'used_load_elements') for ts in tile_stats)
    ))
    print('num ld elements stepped {v}'.format(
        v=sum(value_or_zero(ts, 'stepped_load_elements') for ts in tile_stats)
    ))
    print('num st elements stepped {v}'.format(
        v=sum(value_or_zero(ts, 'stepped_store_elements') for ts in tile_stats)
    ))
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'num_floated') for ts in tile_stats),
        f='num float               {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_sent_slice') for ts in tile_stats),
        f='num llc sent slice      {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_migrated') for ts in tile_stats),
        f='num llc migrated        {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'mlc_response') for ts in tile_stats),
        f='num mlc response        {v}')
    print('num d$ core req         {v}'.format(
        v=sum(value_or_zero(ts, 'dcache_core_requests') for ts in tile_stats)
    ))
    print('num d$ core stream req  {v}'.format(
        v=sum(value_or_zero(ts, 'dcache_core_stream_requests') for ts in tile_stats)
    ))
    print('num llc core req        {v}'.format(
        v=sum(value_or_zero(ts, 'llc_core_requests') for ts in tile_stats)
    ))
    print_if_non_zero(
        v=main_ts.sim_ticks / ticks_per_us,
        f='main cpu us             {v}')
    print_if_non_zero(
        v=main_ts.pum_jit_us,
        f='pum jit us              {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_core_stream_requests') for ts in tile_stats),
        f='num llc core stream req {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_llc_stream_requests') for ts in tile_stats),
        f='num llc llc stream req  {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_llc_ind_stream_requests') for ts in tile_stats),
        f='num llc llc ind req     {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_llc_multicast_stream_requests') for ts in tile_stats),
        f='num llc llc multi req   {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'l2_evicts_noreuse_ctrl_pkts') for ts in tile_stats),
        f='num l2 noreuse ctrl pkt {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'l2_evicts_noreuse_ctrl_evict_pkts') for ts in tile_stats),
        f='num l2 noreuse evic pkt {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'l2_evicts_noreuse_data_pkts') for ts in tile_stats),
        f='num l2 noreuse data pkt {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'llc_llc_multicast_stream_requests') for ts in tile_stats),
        f='num llc llc multi req   {v}')
    print_if_non_zero(
        v=sum([value_or_zero(main_ts.l3_transitions[s], 'L1_GETV') for s in main_ts.l3_transitions]),
        f='num llc GETV event      {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'mem_num_reads') for ts in tile_stats),
        f='num mem reads           {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'mem_bytes_read') for ts in tile_stats),
        f='num mem bytes reads     {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'mem_num_writes') for ts in tile_stats),
        f='num mem writes          {v}')
    print_if_non_zero(
        v=sum(value_or_zero(ts, 'mem_bytes_write') for ts in tile_stats),
        f='num mem bytes writes    {v}')
    print('num core microops       {v}'.format(
        v=sum(value_or_zero(ts, 'core_committed_microops') for ts in tile_stats)
    ))
    print('pum mix cycle           {v}'.format(
        v=value_or_zero(tile_stats[0], 'pum_mix_cycle'),
    ))

    total_stream_data_traffic_fix = sum(value_or_zero(ts, 'stream_data_traffic_fix') for ts in tile_stats)
    if total_stream_data_traffic_fix != 0:
        total_stream_data_traffic_float = sum(value_or_zero(ts, 'stream_data_traffic_float') for ts in tile_stats)
        total_core_data_traffic_fix = sum(value_or_zero(ts, 'core_data_traffic_fix') for ts in tile_stats)
        total_core_data_traffic_fix_ignored = sum(value_or_zero(ts, 'core_data_traffic_fix_ignored') for ts in tile_stats)
        print(f'data traffic           {total_core_data_traffic_fix} {total_core_data_traffic_fix_ignored} {total_stream_data_traffic_fix} {total_stream_data_traffic_float}')

    total_llc_computations = sum(value_or_zero(ts, 'llc_stream_computations') for ts in tile_stats)
    if total_llc_computations != 0:
        print('num llc computations    {total} {v}'.format(
            total=total_llc_computations,
            v=' '.join(str(value_or_zero(ts, 'llc_stream_computations')) for ts in tile_stats),
        ))
    total_atomics = sum(value_or_zero(ts, 'llc_stream_atomics') for ts in tile_stats)
    if total_atomics != 0:
        print('num llc atomics                  {total}'.format(total=total_atomics))
        print('num llc commit atomics           {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_committed_atomics') for ts in tile_stats),
        ))
        print('num llc locked atomics           {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_locked_atomics') for ts in tile_stats),
        ))
        print('num llc unlocked atomics         {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_unlocked_atomics') for ts in tile_stats),
        ))
        print('num llc line conflict atomics    {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_line_conflict_atomics') for ts in tile_stats),
        ))
        print('num llc xaw  conflict atomics    {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_xaw_conflict_atomics') for ts in tile_stats),
        ))
        print('num llc real conflict atomics    {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_real_conflict_atomics') for ts in tile_stats),
        ))
        print('num llc real xaw conflict atomic {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_real_xaw_conflict_atomics') for ts in tile_stats),
        ))
        print('num llc real xaw conflict atomic {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_real_xaw_conflict_atomics') for ts in tile_stats),
        ))
        print('num llc deadlock atomic          {total}'.format(
            total=sum(value_or_zero(ts, 'llc_stream_deadlock_atomics') for ts in tile_stats),
        ))
    for ts in tile_stats:
        atomics = value_or_zero(ts, 'llc_stream_atomics')
        if atomics == 0:
            continue
        atomics_committed = value_or_zero(ts, 'llc_stream_committed_atomics')
        atomics_locked = value_or_zero(ts, 'llc_stream_locked_atomics')
        atomics_unlocked = value_or_zero(ts, 'llc_stream_unlocked_atomics')
        atomics_line_conflict = value_or_zero(ts, 'llc_stream_line_conflict_atomics')
        atomics_real_conflict = value_or_zero(ts, 'llc_stream_real_conflict_atomics')
        atomics_deadlock = value_or_zero(ts, 'llc_stream_deadlock_atomics')
        print(f'Tile {ts.tile_id} Atomic {atomics} Commit {atomics_committed} Lock {atomics_locked} Unlock {atomics_unlocked} Line {atomics_line_conflict} Real {atomics_real_conflict} Deadlock {atomics_deadlock}')

def getPUMJitterRuntime(sim_out_folder, tile_stats):
    total_runtime = PUMJitterExperiments.getPUMJitTimeMicroSecond(sim_out_folder)
    for ts in tile_stats:
        # Set the fields for all tile_stats
        ts.__dict__['pum_jit_us'] = total_runtime


if __name__ == '__main__':
    if 'traffic' in sys.argv:
        __print_traffic__ = True
    with open(sys.argv[1]) as f:
        tile_stats = process(f)
    sim_out_folder = os.path.dirname(sys.argv[1])
    getPUMJitterRuntime(sim_out_folder, tile_stats)
    print_stats(tile_stats)
