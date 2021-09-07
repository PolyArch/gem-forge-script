
def configureMemoryControlDRAMSim3(self, mc, mcpat_mc):
    # ! So far we use the fixed configuration for DDR4_8Gb_x8_3200.ini
    mcpat_mc.number_ranks = 2
    mcpat_mc.llc_line_length = 64

def configureMemoryControl(self):
    # ! Dual channel have two memory controller,
    # ! But mcpat supports only one.
    mc = self.gem5Sys['mem_ctrls'][0]
    mcpat_mc = self.xml.sys.mc
    mcpat_mc.mc_clock = self.toMHz(self.getSystemClockDomain())
    mcpat_mc.memory_channels_per_mc = 1
    if mc['type'] == 'DRAMsim3':
        configureMemoryControlDRAMSim3(self, mc, mcpat_mc)
    else:
        mcpat_mc.number_ranks = mc['ranks_per_channel']
        mcpat_mc.llc_line_length = mc['write_buffer_size']

def setStatsMemoryControl(self):
    # ! I simply sum up all memory controllers
    # ! Even for DRAMSim3 we still use gem5 stats.
    mcs = self.gem5Sys['mem_ctrls']
    memReads = 0
    memWrites = 0
    if len(mcs) > 1:
        for mcId in range(len(mcs)):
            memReads += self.getVecStatsTotal('system.mem_ctrls{i}.num_reads'.format(i=mcId))
            memWrites += self.getVecStatsTotal('system.mem_ctrls{i}.num_writes'.format(i=mcId))
    else:
        memReads = self.getVecStatsTotal("system.mem_ctrls.num_reads")
        memWrites = self.getVecStatsTotal("system.mem_ctrls.num_writes")
    mc = self.xml.sys.mc
    mc.memory_reads = memReads
    mc.memory_writes = memWrites
    mc.memory_accesses = memReads + memWrites