# Copyright (c) 2012, 2017-2018, 2021 ARM Limited
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
# Copyright (c) 2006-2007 The Regents of The University of Michigan
# Copyright (c) 2009 Advanced Micro Devices, Inc.
# All rights reserved.
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

import math
from importlib import import_module

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import (
    addToPath,
    fatal,
)

from gem5.isas import ISA
from gem5.runtime import get_supported_isas

addToPath("../")

from common import (
    FileSystemConfig,
    MemConfig,
    ObjectList,
)
from network import Network
from topologies import *


def define_options(parser):
    # By default, ruby uses the simple timing cpu and the X86 ISA
    parser.set_defaults(cpu_type="X86TimingSimpleCPU")

    parser.add_argument(
        "--ruby-clock",
        action="store",
        type=str,
        default="2GHz",
        help="Clock for blocks running at Ruby system's speed",
    )

    parser.add_argument(
        "--access-backing-store",
        action="store_true",
        default=False,
        help="Should ruby maintain a second copy of memory",
    )

    # Options related to cache structure
    parser.add_argument(
        "--ports",
        action="store",
        type=int,
        default=4,
        help="used of transitions per cycle which is a proxy \
            for the number of ports.",
    )

    # network options are in network/Network.py

    # ruby mapping options
    parser.add_argument(
        "--numa-high-bit",
        type=int,
        default=0,
        help="high order address bit to use for numa mapping. "
        "0 = highest bit, not specified = lowest bit",
    )
    parser.add_argument(
        "--interleaving-bits",
        type=int,
        default=0,
        help="number of bits to specify interleaving "
        "in directory, memory controllers and caches. "
        "0 = not specified",
    )
    parser.add_argument(
        "--xor-low-bit",
        type=int,
        default=20,
        help="hashing bit for channel selection"
        "see MemConfig for explanation of the default"
        "parameter. If set to 0, xor_high_bit is also"
        "set to 0.",
    )

    parser.add_argument(
        "--recycle-latency",
        type=int,
        default=10,
        help="Recycle latency for ruby controller input buffers",
    )

    import_module(f"ruby.{buildEnv['PROTOCOL']}").define_options(parser)

    Network.define_options(parser)


def setup_memory_controllers(system, ruby, dir_cntrls, options):
    if options.numa_high_bit:
        block_size_bits = (
            options.numa_high_bit + 1 - int(math.log(options.num_dirs, 2))
        )
        ruby.block_size_bytes = 2 ** (block_size_bits)
    else:
        ruby.block_size_bytes = options.cacheline_size

    ruby.memory_size_bits = 48

    index = 0
    mem_ctrls = []
    crossbars = []

    if options.numa_high_bit:
        dir_bits = int(math.log(options.num_dirs, 2))
        intlv_size = 2 ** (options.numa_high_bit - dir_bits + 1)
    else:
        # if the numa_bit is not specified, set the directory bits as the
        # lowest bits above the block offset bits
        intlv_size = options.cacheline_size

    # Sets bits to be used for interleaving.  Creates memory controllers
    # attached to a directory controller.  A separate controller is created
    # for each address range as the abstract memory can handle only one
    # contiguous address range as of now.
    for dir_cntrl in dir_cntrls:
        crossbar = None
        if len(system.mem_ranges) > 1:
            crossbar = IOXBar()
            crossbars.append(crossbar)
            dir_cntrl.memory_out_port = crossbar.cpu_side_ports

        dir_ranges = []
        for r in system.mem_ranges:
            mem_type = ObjectList.mem_list.get(options.mem_type)
            dram_intf = MemConfig.create_mem_intf(
                mem_type,
                r,
                index,
                int(math.log(options.num_dirs, 2)),
                intlv_size,
                options.xor_low_bit,
            )
            if issubclass(mem_type, DRAMInterface):
                mem_ctrl = m5.objects.MemCtrl(dram=dram_intf)
            else:
                mem_ctrl = dram_intf

            if options.access_backing_store:
                dram_intf.kvm_map = False

            mem_ctrls.append(mem_ctrl)
            dir_ranges.append(dram_intf.range)

            if crossbar != None:
                mem_ctrl.port = crossbar.mem_side_ports
            else:
                mem_ctrl.port = dir_cntrl.memory_out_port

            # Enable low-power DRAM states if option is set
            if issubclass(mem_type, DRAMInterface):
                mem_ctrl.dram.enable_dram_powerdown = (
                    options.enable_dram_powerdown
                )

        index += 1
        dir_cntrl.addr_ranges = dir_ranges

    system.mem_ctrls = mem_ctrls

    if len(crossbars) > 0:
        ruby.crossbars = crossbars


def create_topology(controllers, options):
    """Called from create_system in configs/ruby/<protocol>.py
    Must return an object which is a subclass of BaseTopology
    found in configs/topologies/BaseTopology.py
    This is a wrapper for the legacy topologies.
    """
    topology_class = getattr(
        import_module(f"topologies.{options.topology}"), options.topology
    )
    topology = topology_class(controllers=controllers)
    return topology


def create_system(
    options,
    full_system,
    system,
    piobus=None,
    dma_ports=[],
    bootmem=None,
    cpus=None,
):
    system.ruby = RubySystem()
    ruby = system.ruby

    # Generate pseudo filesystem
    FileSystemConfig.config_filesystem(system, options)

    # Create the network object
    (
        network,
        IntLinkClass,
        ExtLinkClass,
        RouterClass,
        InterfaceClass,
    ) = Network.create_network(options, ruby)
    ruby.network = network

    if cpus is None:
        cpus = system.cpu

    try:
        (cpu_sequencers, dir_cntrls, topology) = import_module(
            f"ruby.{buildEnv['PROTOCOL']}"
        ).create_system(
            options, full_system, system, dma_ports, bootmem, ruby, cpus
        )
    except:
        print(
            "Error: could not create sytem for ruby protocol "
            f"{buildEnv['PROTOCOL']}"
        )
        raise

    # Create the network topology
    topology.makeTopology(
        options, network, IntLinkClass, ExtLinkClass, RouterClass
    )

    # Register the topology elements with faux filesystem (SE mode only)
    if not full_system:
        topology.registerTopology(options)

    # Initialize network based on topology
    Network.init_network(options, network, InterfaceClass)

    # Create a port proxy for connecting the system port. This is
    # independent of the protocol and kept in the protocol-agnostic
    # part (i.e. here).
    sys_port_proxy = RubyPortProxy(ruby_system=ruby)
    if piobus is not None:
        sys_port_proxy.pio_request_port = piobus.cpu_side_ports

    # Give the system port proxy a SimObject parent without creating a
    # full-fledged controller
    system.sys_port_proxy = sys_port_proxy

    # Connect the system port for loading of binaries etc
    system.system_port = system.sys_port_proxy.in_ports

    setup_memory_controllers(system, ruby, dir_cntrls, options)

    # Connect the cpu sequencers and the piobus
    if piobus != None:
        for cpu_seq in cpu_sequencers:
            cpu_seq.connectIOPorts(piobus)

    ruby.number_of_virtual_networks = ruby.network.number_of_virtual_networks
    ruby._cpu_ports = cpu_sequencers
    ruby.num_of_sequencers = len(cpu_sequencers)

    # Create a backing copy of physical memory in case required
    if options.access_backing_store:
        ruby.access_backing_store = True
        ruby.phys_mem = SimpleMemory(
            range=system.mem_ranges[0], in_addr_map=False
        )


def create_directories(options, bootmem, ruby_system, system):
    import importlib

    try:
        # The supported way to use Ruby is now to use the protocol name as
        # part of the names for all of the controllers. This is *required*
        # when using `MULTIPLE` as the protocol and the `ALL` target.
        Directory_Controller = getattr(
            importlib.import_module("m5.objects"),
            f"{options.protocol}_Directory_Controller",
        )
    except AttributeError:
        # This is a fallback for the legacy Ruby protocols. If you can't
        # find the protocol-specific directory controller, then use the
        # generic one. This is a hack that only works if you have a single
        # protocol.
        Directory_Controller = getattr(
            importlib.import_module("m5.objects"), "Directory_Controller"
        )

    dir_cntrl_nodes = []
    for i in range(options.num_dirs):
        dir_cntrl = Directory_Controller()
        dir_cntrl.version = i
        dir_cntrl.directory = RubyDirectoryMemory(
            block_size=ruby_system.block_size_bytes
        )
        dir_cntrl.ruby_system = ruby_system

        exec("ruby_system.dir_cntrl%d = dir_cntrl" % i)
        dir_cntrl_nodes.append(dir_cntrl)

    if bootmem is not None:
        rom_dir_cntrl = Directory_Controller()
        rom_dir_cntrl.directory = RubyDirectoryMemory(
            block_size=ruby_system.block_size_bytes
        )
        rom_dir_cntrl.ruby_system = ruby_system
        rom_dir_cntrl.version = i + 1
        rom_dir_cntrl.memory = bootmem.port
        rom_dir_cntrl.addr_ranges = bootmem.range
        return (dir_cntrl_nodes, rom_dir_cntrl)

    return (dir_cntrl_nodes, None)


def send_evicts(options):
    # currently, 2 scenarios warrant forwarding evictions to the CPU:
    # 1. The O3 model must keep the LSQ coherent with the caches
    # 2. The x86 mwait instruction is built on top of coherence invalidations
    # 3. The local exclusive monitor in ARM systems
    if get_supported_isas() == {ISA.NULL}:
        return False

    if (
        hasattr(m5.objects, "DerivO3CPU")
        and isinstance(options.cpu_type, DerivO3CPU)
    ) or ObjectList.cpu_list.get_isa(options.cpu_type) in [ISA.X86, ISA.ARM]:
        return True
    return False
