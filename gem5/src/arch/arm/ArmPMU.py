# -*- mode:python -*-
# Copyright (c) 2009-2014, 2017-2018, 2020, 2022-2023, 2025 Arm Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.defines import buildEnv
from m5.objects.Gic import (
    ArmInterruptPin,
    ArmPPI,
)
from m5.params import *
from m5.params import isNullPointer
from m5.proxy import *
from m5.SimObject import *
from m5.util.fdthelper import *


class EventTypeId(Enum):
    """
    The values of the scoped enum are matching the event ID
    number defined in the Arm architecture reference manual
    """

    map = {
        "SW_INCR": 0x00,
        "L1I_CACHE_REFILL": 0x01,
        "L1I_TLB_REFILL": 0x02,
        "L1D_CACHE_REFILL": 0x03,
        "L1D_CACHE": 0x04,
        "L1D_TLB_REFILL": 0x05,
        "LD_RETIRED": 0x06,
        "ST_RETIRED": 0x07,
        "INST_RETIRED": 0x08,
        "EXC_TAKEN": 0x09,
        "EXC_RETURN": 0x0A,
        "CID_WRITE_RETIRED": 0x0B,
        "PC_WRITE_RETIRED": 0x0C,
        "BR_IMMED_RETIRED": 0x0D,
        "BR_RETURN_RETIRED": 0x0E,
        "UNALIGEND_LDST_RETIRED": 0x0F,
        "BR_MIS_PRED": 0x10,
        "CPU_CYCLES": 0x11,
        "BR_PRED": 0x12,
        "MEM_ACCESS": 0x13,
        "L1I_CACHE": 0x14,
        "L1D_CACHE_WB": 0x15,
        "L2D_CACHE": 0x16,
        "L2D_CACHE_REFILL": 0x17,
        "L2D_CACHE_WB": 0x18,
        "BUS_ACCESS": 0x19,
        "MEMORY_ERROR": 0x1A,
        "INST_SPEC": 0x1B,
        "TTBR_WRITE_RETIRED": 0x1C,
        "BUS_CYCLES": 0x1D,
        "CHAIN": 0x1E,
        "L1D_CACHE_ALLOCATE": 0x1F,
        "L2D_CACHE_ALLOCATE": 0x20,
        "BR_RETIRED": 0x21,
        "BR_MIS_PRED_RETIRED": 0x22,
        "STALL_FRONTEND": 0x23,
        "STALL_BACKEND": 0x24,
        "L1D_TLB": 0x25,
        "L1I_TLB": 0x26,
        "L2I_CACHE": 0x27,
        "L2I_CACHE_REFILL": 0x28,
        "L3D_CACHE_ALLOCATE": 0x29,
        "L3D_CACHE_REFILL": 0x2A,
        "L3D_CACHE": 0x2B,
        "L3D_CACHE_WB": 0x2C,
        "L2D_TLB_REFILL": 0x2D,
        "L2I_TLB_REFILL": 0x2E,
        "L2D_TLB": 0x2F,
        "L2I_TLB": 0x30,
        "INVALID": 0xFF,
    }


class ProbeEvent:
    def __init__(self, pmu, _eventId, obj, *listOfNames):
        self.obj = obj
        self.names = listOfNames
        self.eventId = EventTypeId(_eventId).getValue()
        self.pmu = pmu

    def register(self):
        if self.obj:
            for name in self.names:
                self.pmu.getCCObject().addEventProbe(
                    self.eventId, self.obj.getCCObject(), name
                )


class SoftwareIncrement:
    def __init__(self, pmu, _eventId):
        self.eventId = EventTypeId(_eventId).getValue()
        self.pmu = pmu

    def register(self):
        self.pmu.getCCObject().addSoftwareIncrementEvent(self.eventId)


class ArmPMU(SimObject):
    type = "ArmPMU"
    cxx_class = "gem5::ArmISA::PMU"
    cxx_header = "arch/arm/pmu.hh"

    cxx_exports = [
        PyBindMethod("addEventProbe"),
        PyBindMethod("addSoftwareIncrementEvent"),
    ]

    _events = None

    def addEvent(self, newObject):
        if not (
            isinstance(newObject, ProbeEvent)
            or isinstance(newObject, SoftwareIncrement)
        ):
            raise TypeError(
                "argument must be of ProbeEvent or SoftwareIncrement type"
            )

        if not self._events:
            self._events = []

        self._events.append(newObject)

    # Override the normal SimObject::regProbeListeners method and
    # register deferred event handlers.
    def regProbeListeners(self):
        for event in self._events:
            event.register()

        self.getCCObject().regProbeListeners()

    def addArchEvents(
        self,
        cpu=None,
        itb=None,
        dtb=None,
        icache=None,
        dcache=None,
        l2cache=None,
    ):
        """Add architected events to the PMU.

        This method can be called multiple times with only a subset of
        the keyword arguments set. This enables event registration in
        configuration scripts to happen closer to the instantiation of
        the instrumented objects (e.g., the memory system) instead of
        a central point.

        CPU events should also be registered once per CPU that is
        sharing the PMU (e.g., when switching between CPU models).
        """

        bpred = getattr(cpu, "branchPred", None) if cpu else None
        if bpred is not None and isNullPointer(bpred):
            bpred = None

        self.addEvent(SoftwareIncrement(self, "SW_INCR"))
        self.addEvent(ProbeEvent(self, "L1I_CACHE_REFILL", icache, "Fill"))
        self.addEvent(ProbeEvent(self, "L1I_TLB_REFILL", itb, "Refills"))
        self.addEvent(ProbeEvent(self, "L1D_CACHE_REFILL", dcache, "Fill"))
        self.addEvent(ProbeEvent(self, "L1D_CACHE", dcache, "Hit", "Miss"))
        self.addEvent(ProbeEvent(self, "L1D_TLB_REFILL", dtb, "Refills"))
        self.addEvent(ProbeEvent(self, "LD_RETIRED", cpu, "RetiredLoads"))
        self.addEvent(ProbeEvent(self, "ST_RETIRED", cpu, "RetiredStores"))
        self.addEvent(ProbeEvent(self, "INST_RETIRED", cpu, "RetiredInsts"))
        # 0x09: EXC_TAKEN
        # 0x0A: EXC_RETURN
        # 0x0B: CID_WRITE_RETIRED
        # 0x0C: PC_WRITE_RETIRED
        # 0x0D: BR_IMMED_RETIRED
        # 0x0E: BR_RETURN_RETIRED
        # 0x0F: UNALIGEND_LDST_RETIRED
        self.addEvent(ProbeEvent(self, "BR_MIS_PRED", bpred, "Misses"))
        self.addEvent(ProbeEvent(self, "CPU_CYCLES", cpu, "ActiveCycles"))
        self.addEvent(ProbeEvent(self, "BR_PRED", bpred, "Branches"))
        self.addEvent(
            ProbeEvent(
                self, "MEM_ACCESS", cpu, "RetiredLoads", "RetiredStores"
            )
        )
        self.addEvent(ProbeEvent(self, "L1I_CACHE", icache, "Hit", "Miss"))
        # 0x15: L1D_CACHE_WB
        self.addEvent(ProbeEvent(self, "L2D_CACHE", l2cache, "Hit", "Miss"))
        self.addEvent(ProbeEvent(self, "L2D_CACHE_REFILL", l2cache, "Fill"))
        # 0x18: L2D_CACHE_WB
        # 0x19: BUS_ACCESS
        # 0x1A: MEMORY_ERROR
        # 0x1B: INST_SPEC
        # 0x1C: TTBR_WRITE_RETIRED
        # 0x1D: BUS_CYCLES
        # 0x1E: CHAIN
        # 0x1F: L1D_CACHE_ALLOCATE
        # 0x20: L2D_CACHE_ALLOCATE
        self.addEvent(ProbeEvent(self, "BR_RETIRED", cpu, "RetiredBranches"))
        # 0x22: BR_MIS_PRED_RETIRED
        # 0x23: STALL_FRONTEND
        # 0x24: STALL_BACKEND
        # 0x25: L1D_TLB
        # 0x26: L1I_TLB
        # 0x27: L2I_CACHE
        # 0x28: L2I_CACHE_REFILL
        # 0x29: L3D_CACHE_ALLOCATE
        # 0x2A: L3D_CACHE_REFILL
        # 0x2B: L3D_CACHE
        # 0x2C: L3D_CACHE_WB
        # 0x2D: L2D_TLB_REFILL
        # 0x2E: L2I_TLB_REFILL
        # 0x2F: L2D_TLB
        # 0x30: L2I_TLB

    def generateDeviceTree(self, state):
        # For simplicity we just support PPIs for DTB autogen otherwise
        # it would be difficult to construct a ordered list of SPIs
        assert isinstance(self.interrupt, ArmPPI)

        node = FdtNode("pmu")
        node.appendCompatible("arm,armv8-pmuv3")

        gic = self.platform.unproxy(self).gic
        node.append(
            FdtPropertyWords(
                "interrupts", self.interrupt.generateFdtProperty(gic)
            )
        )

        yield node

    cycleEventId = Param.EventTypeId("CPU_CYCLES", "Cycle event id")
    platform = Param.Platform(Parent.any, "Platform this device is part of.")
    eventCounters = Param.Int(31, "Number of supported PMU counters")
    interrupt = Param.ArmInterruptPin("PMU interrupt")
    exitOnPMUControl = Param.Bool(
        False, "Exit on PMU enable, disable, or reset"
    )
    exitOnPMUInterrupt = Param.Bool(False, "Exit on PMU interrupt")

    # 64-bit PMU event counters are officially supported when
    # Armv8.5-A FEAT_PMUv3p5 is implemented. This parameter is not a
    # full implementation of FEAT_PMUv3p5.
    use64bitCounters = Param.Bool(
        False,
        "Choose whether to use 64-bit or 32-bit PMEVCNTR<n>_EL0 registers.",
    )

    statCounters = DictParam.Int.String(
        {},
        """
        Dictionary of PMU events to be merged into the stats framework.
            Key = ID of the PMU event
            Value = Name of the gem5 stat

        For example the following param value:

        my_stat_counters = {
            int(EventTypeId("INST_RETIRED")): "INST_RETIRED",
            int(EventTypeId("CPU_CYCLES")): "CPU_CYCLES",
            0xC0C0 : "MY_IMPDEF_EVENT"
        }

        Will produce three stats under the pmu section:
            root.<>.pmu.INST_RETIRED=<val>
            root.<>.pmu.CPU_CYCLES=<val>
            root.<>.pmu.MY_IMPDEF_EVENT=<val>
        """,
    )
