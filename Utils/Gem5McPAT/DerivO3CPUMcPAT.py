
def configureDerivO3CPU(self, cpu):
    idx = cpu.cpu_id
    core = self.xml.sys.core[idx]
    core.clock_rate = self.toMHz(self.getCPUClockDomain())
    isaType = cpu.isa[0].type
    core.x86 = isaType == 'X86ISA'

    core.fetch_width = cpu.fetchWidth
    core.decode_width = cpu.decodeWidth
    # Make the peak issueWidth the same as issueWidth.
    core.issue_width = cpu.issueWidth
    core.peak_issue_width = cpu.issueWidth
    core.commit_width = cpu.commitWidth

    # There is no float issue width in gem5.
    # Make it min(issueWidth, numFPU).
    core.fp_issue_width = min(cpu.issueWidth, 6)

    # Integer pipeline and float pipeline depth.
    intExe = 3
    fpExe = 6
    if isaType == 'X86ISA':
      intExe = 2
      fpExe = 8
    elif isaType == 'ArmISA':
      intExe = 3
      fpExe = 7
    baseStages = cpu.fetchToDecodeDelay + cpu.decodeToRenameDelay + \
                     cpu.renameToIEWDelay + cpu.iewToCommitDelay
    maxBaseStages = \
        max(cpu.commitToDecodeDelay, cpu.commitToFetchDelay,
            cpu.commitToIEWDelay, cpu.commitToRenameDelay)

    # ! PyBind will copy it.
    pipeline_depth = core.pipeline_depth
    pipeline_depth[0] = intExe + baseStages + maxBaseStages
    pipeline_depth[1] = fpExe + baseStages + maxBaseStages
    core.pipeline_depth = pipeline_depth

    core.instruction_buffer_size = cpu.fetchBufferSize

    # Again gem5 does not distinguish int/fp instruction window.
    core.instruction_window_size = cpu.numIQEntries
    core.fp_instruction_window_size = cpu.numIQEntries

    core.ROB_size = cpu.numROBEntries
    core.phy_Regs_IRF_size = cpu.numPhysIntRegs
    core.phy_Regs_FRF_size = cpu.numPhysFloatRegs
    core.store_buffer_size = cpu.SQEntries
    core.load_buffer_size = cpu.LQEntries

    # X86 ONLY
    core.opt_local = 0
    core.instruction_length = 32
    core.opcode_width = 16
    core.micro_opcode_width = 8
    core.machine_type = 0; # 0 for O3.

    # Instruction TLB.
    try:
        mcpatITLB = core.itlb
        mcpatITLB.number_entries = self.getTLBSize(cpu.mmu.itb)
    except AttributeError:
        print('Warn! Failed to configure ITLB.')

    # Data TLB.
    try:
        mcpatDTLB = core.dtlb
        mcpatDTLB.number_entries = self.getTLBSize(cpu.mmu.dtb)
    except AttributeError:
        print('Warn! Failed to configure DTLB.')

    # L1 directory.
    mcpatL1Directory = self.xml.sys.L1Directory[idx]
    mcpatL1Directory.clockrate = self.toMHz(self.getCPUClockDomain())

def setStatsDerivO3CPU(self, cpu):
    """
    Gem5 stats changed the name from future_cpus00 -> future_cpus0.
    """
    def replace_path(path):
        for suffix in [f'0{x}' for x in range(10)]:
            if path.endswith(suffix):
                return f'{path[:-2]}{cpu.cpu_id}'
        return path
    old_cpu_path = cpu.path
    new_cpu_path = replace_path(cpu.path)

    core = self.xml.sys.core[cpu.cpu_id]
    print(f'CPU.Path old {old_cpu_path} new {new_cpu_path}')
    def scalar(stat): return self.getScalarStats(cpu.path + '.' + stat)
    def vector(stat): return self.getVecStatsTotal(cpu.path + '.' + stat)
    def scalar2(stat): return self.getScalarStats(new_cpu_path + '.' + stat)
    def vector2(stat): return self.getVecStatsTotal(new_cpu_path + '.' + stat)

    decodedInsts = scalar2("decode.decodedInsts")
    branchInsts = scalar2("fetch.branches")
    loadInsts = scalar2("iew.dispLoadInsts")
    storeInsts = scalar2("iew.dispStoreInsts")
    commitInsts = scalar2("commit.opsCommitted")
    commitIntInsts = scalar2("commit.integer")
    commitFpInsts = scalar2("commit.floating")
    totalCycles = scalar2("numCycles")
    idleCycles = scalar2("idleCycles")
    robReads = scalar2("rob.reads")
    robWrites = scalar2("rob.writes")

    # Gem5 seems not distinguish rename int/fp operands.
    # Just make rename float writes 0.
    renameWrites = scalar2("rename.renamedOperands")
    renameReads = scalar2("rename.lookups")
    renameFpReads = scalar2("rename.fpLookups")
    renameFpWrites = 0

    instWinReads = scalar2("intInstQueueReads")
    instWinWrites = scalar2("intInstQueueWrites")
    instWinWakeUpAccesses = scalar2("intInstQueueWakeupAccesses")
    instWinFpReads = scalar2("fpInstQueueReads")
    instWinFpWrites = scalar2("fpInstQueueWrites")
    instWinFpWakeUpAccesses = scalar2("fpInstQueueWakeupAccesses")

    intRegReads = scalar2("intRegfileReads")
    intRegWrites = scalar2("intRegfileWrites")
    fpRegReads = scalar2("fpRegfileReads")
    fpRegWrites = scalar2("fpRegfileWrites")

    commitCalls = scalar2("commit.functionCalls")

    intALU = scalar2("intAluAccesses")
    fpALU = scalar2("fpAluAccesses")
    # auto multi = this->getHistStats()
    multi = 0.0
    divs = 0.0
    multiAndDiv = multi + divs
    intALU -= multiAndDiv

    core.total_instructions = decodedInsts
    core.int_instructions = 0
    core.fp_instructions = 0
    core.branch_instructions = branchInsts
    core.branch_mispredictions = 0
    core.committed_instructions = commitInsts
    core.committed_int_instructions = commitIntInsts
    core.committed_fp_instructions = commitFpInsts
    core.load_instructions = loadInsts
    core.store_instructions = storeInsts
    core.total_cycles = totalCycles
    core.idle_cycles = idleCycles
    core.busy_cycles = totalCycles - idleCycles
    core.instruction_buffer_reads = 0
    core.instruction_buffer_write = 0
    core.ROB_reads = robReads
    core.ROB_writes = robWrites

    core.rename_reads = renameReads
    core.rename_writes = renameWrites
    core.fp_rename_reads = renameFpReads
    core.fp_rename_writes = renameFpWrites

    core.inst_window_reads = instWinReads
    core.inst_window_writes = instWinWrites
    core.inst_window_wakeup_accesses = instWinWakeUpAccesses
    core.inst_window_selections = 0
    core.fp_inst_window_reads = instWinFpReads
    core.fp_inst_window_writes = instWinFpWrites
    core.fp_inst_window_wakeup_accesses = instWinFpWakeUpAccesses
    core.fp_inst_window_selections = 0
    core.archi_int_regfile_reads = 0
    core.archi_float_regfile_reads = 0
    core.phy_int_regfile_reads = 0
    core.phy_float_regfile_reads = 0
    core.phy_int_regfile_writes = 0
    core.phy_float_regfile_writes = 0
    core.archi_int_regfile_writes = 0
    core.archi_float_regfile_writes = 0
    core.int_regfile_reads = intRegReads
    core.float_regfile_reads = fpRegReads
    core.int_regfile_writes = intRegWrites
    core.float_regfile_writes = fpRegWrites
    core.windowed_reg_accesses = 0
    core.windowed_reg_transports = 0
    core.function_calls = commitCalls
    core.context_switches = 0
    core.ialu_accesses = intALU
    core.fpu_accesses = fpALU
    core.mul_accesses = multiAndDiv
    core.cdb_alu_accesses = intALU
    core.cdb_mul_accesses = multiAndDiv
    core.cdb_fpu_accesses = fpALU
    core.load_buffer_reads = 0
    core.load_buffer_writes = 0
    core.load_buffer_cams = 0
    core.store_buffer_reads = 0
    core.store_buffer_writes = 0
    core.store_buffer_cams = 0
    core.store_buffer_forwards = 0
    core.main_memory_access = 0
    core.main_memory_read = 0
    core.main_memory_write = 0
    core.pipeline_duty_cycle = 0
