# Copyright (c) 2019 ARM Limited
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
# Copyright (c) 2008 The Hewlett-Packard Development Company
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

import os
import sys
from pathlib import Path

import m5

from _m5.core import setOutputDir
from _m5.loader import setInterpDir

"""
This function is meant to have a similar functionality to override_outdir in
src/python/gem5/simulate/simulator.py. It changes the output directory for
simerr.txt and simout.txt, which are generated when the -re flag is passed to
gem5 in the command line. This function is primarily for use with multisim.

Code copied and adapted from main.py
"""


def override_re_outdir(new_outdir):
    options = m5.options

    stdout_file = Path(new_outdir) / "simout.txt"
    stderr_file = Path(new_outdir) / "simerr.txt"
    if options.redirect_stdout:
        redir_fd = os.open(stdout_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(redir_fd, sys.stdout.fileno())
        if not options.redirect_stderr:
            os.dup2(redir_fd, sys.stderr.fileno())
    if options.redirect_stderr:
        redir_fd = os.open(stderr_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(redir_fd, sys.stderr.fileno())
