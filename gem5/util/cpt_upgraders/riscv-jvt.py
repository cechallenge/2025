# Copyright (c) 2024 Arm Limited
# All rights reserved
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
# Copyright (c) 2023 Barcelona Supercomputing Center (BSC)
# All rights reserved.

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


def upgrader(cpt):
    """
    Add JVT misc registers in the checkpoint
    """

    import re

    for sec in cpt.sections():
        # Search for all XC sections
        res = re.search(r"(.*processor.*\.core.*)\.xc.*", sec)
        if res and cpt.get(res.groups()[0] + ".isa", "isaName") == "riscv":
            # Update for RISCV XCs
            if cpt.get(sec, "_zcmtSecondFetch", fallback="") == "":
                cpt.set(sec, "_zcmtSecondFetch", "false")

            if cpt.get(sec, "_zcmtPc", fallback="") == "":
                cpt.set(sec, "_zcmtPc", "0")

        # Search for all ISA sections
        res = re.search(r".*processor.*\.core.*\.isa$", sec)
        if res and cpt.get(sec, "isaName") == "riscv":
            # Updating jvt misc registers (dummy values)
            mr = cpt.get(sec, "miscRegFile").split()
            if len(mr) >= 170:
                print(
                    "MISCREG_* Zcmt registers already seem " "to be inserted."
                )
            else:
                # Add dummy value for MISCREG_JVT, where idx is
                # NUM_PHYS_MISCREGS - 1
                mr.insert(len(mr) - 1, 0)
                cpt.set(sec, "miscRegFile", " ".join(str(x) for x in mr))


legacy_version = 19
