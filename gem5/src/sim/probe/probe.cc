/*
 * Copyright (c) 2013 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2020 Inria
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "sim/probe/probe.hh"

#include "debug/ProbeVerbose.hh"

namespace gem5
{

ProbePoint::ProbePoint(ProbeManager *manager, const std::string& _name)
    : name(_name)
{
    if (manager) {
        manager->addPoint(*this);
    }
}

bool
ProbeManager::addListener(std::string_view point_name, ProbeListener &listener)
{
    DPRINTFR(ProbeVerbose, "Probes: Call to addListener to \"%s\" on %s.\n",
        point_name, name());
    bool added = false;
    for (auto p = points.begin(); p != points.end(); ++p) {
        if ((*p)->getName() == point_name) {
            (*p)->addListener(&listener);
            added = true;
        }
    }
    if (!added) {
        DPRINTFR(ProbeVerbose, "Probes: Call to addListener to \"%s\" on "
            "%s failed, no such point.\n", point_name, name());
    }
    return added;
}

bool
ProbeManager::removeListener(std::string_view point_name,
                             ProbeListener &listener)
{
    DPRINTFR(ProbeVerbose, "Probes: Call to removeListener from \"%s\" on "
        "%s.\n", point_name, name());
    bool removed = false;
    for (auto p = points.begin(); p != points.end(); ++p) {
        if ((*p)->getName() == point_name) {
            (*p)->removeListener(&listener);
            removed = true;
        }
    }
    if (!removed) {
        DPRINTFR(ProbeVerbose, "Probes: Call to removeListener from \"%s\" "
            "on %s failed, no such point.\n", point_name, name());
    }
    return removed;
}

void
ProbeManager::addPoint(ProbePoint &point)
{
    DPRINTFR(ProbeVerbose, "Probes: Call to addPoint \"%s\" to %s.\n",
        point.getName(), name());

    if (getFirstProbePoint(point.getName())) {
        DPRINTFR(ProbeVerbose, "Probes: Call to addPoint \"%s\" to %s "
                 "failed, already added.\n", point.getName(), name());
        return;
    }
    points.push_back(&point);
}

ProbePoint *
ProbeManager::getFirstProbePoint(std::string_view point_name) const
{
    for (auto p : points) {
        if (p->getName() == point_name) {
            return p;
        }
    }
    return nullptr;
}

} // namespace gem5
