"""
Fix the future_cpus00 -> future_cpus0
"""
def replace_path(path):
    for suffix in [f'0{x}' for x in range(10)]:
        idx = path.find(suffix)
        if idx == -1:
            continue
        return f'{path[:idx]}{path[idx+1:]}'
    return path

def setStatsDTLB(self, tlb, cpuId):
    tlb_path = replace_path(tlb.path)
    def scalar(stat): return self.getScalarStats(tlb_path + '.' + stat)
    reads = scalar("rdAccesses")
    readMisses = scalar("rdMisses")
    writes = scalar("wrAccesses")
    writeMisses = scalar("wrMisses")
    core = self.xml.sys.core[cpuId]
    core.dtlb.total_accesses = reads + writes
    core.dtlb.read_accesses = reads
    core.dtlb.write_accesses = writes
    core.dtlb.read_misses = readMisses
    core.dtlb.write_misses = writeMisses
    core.dtlb.total_misses = readMisses + writeMisses

def setStatsITLB(self, tlb, cpuId):
    tlb_path = replace_path(tlb.path)
    def scalar(stat): return self.getScalarStats(tlb_path + '.' + stat)
    reads = scalar("rdAccesses")
    readMisses = scalar("rdMisses")
    writes = scalar("wrAccesses")
    writeMisses = scalar("wrMisses")
    core = self.xml.sys.core[cpuId]
    core.itlb.total_accesses = reads + writes
    core.itlb.total_misses = readMisses + writeMisses
  