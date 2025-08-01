/*
 * Copyright (c) 2016-2021 Advanced Micro Devices, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 * contributors may be used to endorse or promote products derived from this
 * software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include "arch/amdgpu/vega/insts/op_encodings.hh"

#include <iomanip>

namespace gem5
{

namespace VegaISA
{
    // --- Inst_SOP2 base class methods ---

    Inst_SOP2::Inst_SOP2(InFmt_SOP2 *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);

        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
        } else {
            varSize = 4;
        } // if
    } // Inst_SOP2

    void
    Inst_SOP2::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SSRC0;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(instData.SSRC0), false, false);
        opNum++;

        reg = instData.SSRC1;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(instData.SSRC1), false, false);
        opNum++;

        reg = instData.SDST;
        dstOps.emplace_back(reg, getOperandSize(opNum), false,
                              isScalarReg(instData.SDST), false, false);

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_SOP2::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_SOP2::hasSecondDword(InFmt_SOP2 *iFmt)
    {
        if (iFmt->SSRC0 == REG_SRC_LITERAL)
            return true;

        if (iFmt->SSRC1 == REG_SRC_LITERAL)
            return true;

        return false;
    }

    void
    Inst_SOP2::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        dis_stream << opSelectorToRegSym(instData.SDST) << ", ";

        if (instData.SSRC0 == REG_SRC_LITERAL) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << _srcLiteral << ", ";
        } else {
            dis_stream << opSelectorToRegSym(instData.SSRC0) << ", ";
        }

        if (instData.SSRC1 == REG_SRC_LITERAL) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << _srcLiteral;
        } else {
            dis_stream << opSelectorToRegSym(instData.SSRC1);
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_SOPK base class methods ---

    Inst_SOPK::Inst_SOPK(InFmt_SOPK *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);

        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
        } else {
            varSize = 4;
        } // if
    } // Inst_SOPK

    Inst_SOPK::~Inst_SOPK()
    {
    } // ~Inst_SOPK

    void
    Inst_SOPK::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SDST;
        if (numSrcRegOperands() == getNumOperands()) {
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                isScalarReg(reg), false, false);
            opNum++;
        }

        reg = instData.SIMM16;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, false, true);
        opNum++;

        if (numDstRegOperands()) {
            reg = instData.SDST;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  isScalarReg(reg), false, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_SOPK::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_SOPK::hasSecondDword(InFmt_SOPK *iFmt)
    {
        /*
          SOPK can be a 64-bit instruction, i.e., have a second dword:
          S_SETREG_IMM32_B32 writes some or all of the LSBs of a 32-bit
          literal constant into a hardware register;
          the way to detect such special case is to explicitly check the
          opcode (20/0x14)
        */
        if (iFmt->OP == 0x14)
            return true;

        return false;
    }


    void
    Inst_SOPK::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        // S_SETREG_IMM32_B32 is a 64-bit instruction, using a
        // 32-bit literal constant
        if (instData.OP == 0x14) {
            dis_stream << "0x" << std::hex << std::setfill('0')
                    << std::setw(8) << extData.imm_u32 << ", ";
        } else {
            dis_stream << opSelectorToRegSym(instData.SDST) << ", ";
        }

        dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(4)
                     << instData.SIMM16;

        disassembly = dis_stream.str();
    }

    // --- Inst_SOP1 base class methods ---

    Inst_SOP1::Inst_SOP1(InFmt_SOP1 *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);

        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
        } else {
            varSize = 4;
        } // if
    } // Inst_SOP1

    Inst_SOP1::~Inst_SOP1()
    {
    } // ~Inst_SOP1

    void
    Inst_SOP1::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SSRC0;
        /*
          S_GETPC_B64 does not use SSRC0, so don't put anything on srcOps
          for it (0x1c is 29 base 10, which is the opcode for S_GETPC_B64).
         */
        if (instData.OP != 0x1C) {
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  isScalarReg(instData.SSRC0), false, false);
            opNum++;
        }

        /*
          S_SETPC_B64, S_RFE_B64, S_CBRANCH_JOIN, and S_SET_GPR_IDX_IDX do not
          use SDST, so don't put anything on dstOps for them.
        */
        if ((instData.OP != 0x1D) /* S_SETPC_B64 (29 base 10) */ &&
            (instData.OP != 0x1F) /* S_RFE_B64 (31 base 10) */ &&
            (instData.OP != 0x2E) /* S_CBRANCH_JOIN (46 base 10) */ &&
            (instData.OP != 0x32)) /* S_SET_GPR_IDX_IDX (50 base 10) */ {
          reg = instData.SDST;
          dstOps.emplace_back(reg, getOperandSize(opNum), false,
                              isScalarReg(instData.SDST), false, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_SOP1::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_SOP1::hasSecondDword(InFmt_SOP1 *iFmt)
    {
        if (iFmt->SSRC0 == REG_SRC_LITERAL)
            return true;

        return false;
    }

    void
    Inst_SOP1::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        dis_stream << opSelectorToRegSym(instData.SDST) << ", ";

        if (instData.SSRC0 == REG_SRC_LITERAL) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << extData.imm_u32;
        } else {
            dis_stream << opSelectorToRegSym(instData.SSRC0);
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_SOPC base class methods ---

    Inst_SOPC::Inst_SOPC(InFmt_SOPC *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);

        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
        } else {
            varSize = 4;
        } // if
    } // Inst_SOPC

    Inst_SOPC::~Inst_SOPC()
    {
    } // ~Inst_SOPC

    void
    Inst_SOPC::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SSRC0;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(instData.SSRC0), false, false);
        opNum++;

        reg = instData.SSRC1;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(instData.SSRC1), false, false);

    }

    int
    Inst_SOPC::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_SOPC::hasSecondDword(InFmt_SOPC *iFmt)
    {
        if (iFmt->SSRC0 == REG_SRC_LITERAL)
            return true;

        if (iFmt->SSRC1 == REG_SRC_LITERAL)
            return true;

        return false;
    }

    void
    Inst_SOPC::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        if (instData.SSRC0 == REG_SRC_LITERAL) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << extData.imm_u32;
        } else {
            dis_stream << opSelectorToRegSym(instData.SSRC0) << ", ";
        }

        if (instData.SSRC1 == REG_SRC_LITERAL) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << extData.imm_u32;
        } else {
            dis_stream << opSelectorToRegSym(instData.SSRC1);
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_SOPP base class methods ---

    Inst_SOPP::Inst_SOPP(InFmt_SOPP *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);

        // copy first instruction DWORD
        instData = iFmt[0];
    } // Inst_SOPP

    Inst_SOPP::~Inst_SOPP()
    {
    } // ~Inst_SOPP

    void
    Inst_SOPP::initOperandInfo()
    {
        int opNum = 0;


        if (numSrcRegOperands()) {
            // Needed because can't take addr of bitfield
            int reg = instData.SIMM16;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, false, true);

            opNum++;

            if (readsVCC()) {
                srcOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), true,
                                      true, false, false);
                opNum++;
            }
        }
        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_SOPP::instSize() const
    {
        return 4;
    } // instSize

    void
    Inst_SOPP::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode;

        switch (instData.OP) {
          case 8:
            {
                dis_stream << " ";
                int dest = 4 * instData.SIMM16 + 4;
                dis_stream << "label_" << std::hex << dest;
            }
             break;
          case 12:
            {
                dis_stream << " ";

                int vm_cnt = 0;
                int exp_cnt = 0;
                int lgkm_cnt = 0;

                vm_cnt = bits<uint16_t>(instData.SIMM16, 3, 0);
                exp_cnt = bits<uint16_t>(instData.SIMM16, 6, 4);
                lgkm_cnt = bits<uint16_t>(instData.SIMM16, 11, 8);

                // if the counts are not maxed out, then we
                // print out the count value
                if (vm_cnt != 0xf) {
                    dis_stream << "vmcnt(" << vm_cnt << ")";
                }

                if (lgkm_cnt != 0xf) {
                    if (vm_cnt != 0xf)
                        dis_stream << " & ";

                    dis_stream << "lgkmcnt(" << lgkm_cnt << ")";
                }

                if (exp_cnt != 0x7) {
                    if (vm_cnt != 0xf || lgkm_cnt != 0xf)
                        dis_stream << " & ";

                    dis_stream << "expcnt(" << exp_cnt << ")";
                }
            }
            break;
          default:
            break;
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_SMEM base class methods ---

    Inst_SMEM::Inst_SMEM(InFmt_SMEM *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(Scalar);
        setFlag(GlobalSegment);

        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_SMEM_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);

        if (instData.GLC)
            setFlag(GloballyCoherent);
    } // Inst_SMEM

    Inst_SMEM::~Inst_SMEM()
    {
    } // ~Inst_SMEM

    void
    Inst_SMEM::initOperandInfo()
    {
        // Formats:
        // 0 src + 0 dst
        // 3 src + 0 dst
        // 2 src + 1 dst
        // 0 src + 1 dst
        int opNum = 0;
        // Needed because can't take addr of bitfield
        int reg = 0;

        if (numSrcRegOperands()) {
            reg = instData.SDATA;
            if (numSrcRegOperands() == getNumOperands()) {
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      isScalarReg(reg), false, false);
                opNum++;
            }

            reg = instData.SBASE;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  true, false, false);
            opNum++;

            reg = extData.OFFSET;
            if (instData.IMM) {
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      false, false, true);
            } else {
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      isScalarReg(reg), false, false);
            }
            opNum++;
        }

        if (numDstRegOperands()) {
            reg = instData.SDATA;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  isScalarReg(reg), false, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_SMEM::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_SMEM::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        if (numDstRegOperands()) {
            if (getOperandSize(getNumOperands() - 1) > 4) {
                dis_stream << "s[" << instData.SDATA << ":"
                    << instData.SDATA + getOperandSize(getNumOperands() - 1) /
                    4 - 1 << "], ";
            } else {
                dis_stream << "s" << instData.SDATA << ", ";
            }
        }

        // SBASE has an implied LSB of 0, so we need
        // to shift by one to get the actual value
        dis_stream << "s[" << (instData.SBASE << 1) << ":"
               << ((instData.SBASE << 1) + 1) << "], ";

        if (instData.IMM) {
            // IMM == 1 implies OFFSET should be
            // used as the offset
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(2)
                       << extData.OFFSET;
        } else {
            // IMM == 0 implies OFFSET should be
            // used to specify SGRP in which the
            // offset is held
            dis_stream << "s" << extData.OFFSET;
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_VOP2 base class methods ---

    Inst_VOP2::Inst_VOP2(InFmt_VOP2 *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
            if (iFmt->SRC0 == REG_SRC_DPP) {
                setFlag(IsDPP);
            } else if (iFmt->SRC0 == REG_SRC_SWDA) {
                setFlag(IsSDWA);
            }
        } else {
            varSize = 4;
        } // if
    } // Inst_VOP2

    Inst_VOP2::~Inst_VOP2()
    {
    } // ~Inst_VOP2

    void
    Inst_VOP2::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SRC0;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(reg), isVectorReg(reg), false);
        opNum++;

        reg = instData.VSRC1;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        // VCC read
        if (readsVCC()) {
            srcOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), true,
                                  true, false, false);
            opNum++;
        }

        // VDST
        reg = instData.VDST;
        dstOps.emplace_back(reg, getOperandSize(opNum), false,
                              false, true, false);
        opNum++;

        // VCC write
        if (writesVCC()) {
            dstOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), false,
                                  true, false, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOP2::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_VOP2::hasSecondDword(InFmt_VOP2 *iFmt)
    {
        /*
          There are a few cases where VOP2 instructions have a second dword:

            1.  SRC0 is a literal
            2.  SRC0 is being used to add a data parallel primitive (DPP)
            operation to the instruction.
            3.  SRC0 is being used for sub d-word addressing (SDWA) of the
            operands in the instruction.
            4.  VOP2 instructions also have four special opcodes:',
            V_MADMK_{F16, F32} (0x24, 0x17), and V_MADAK_{F16, F32}',
            (0x25, 0x18), that are always 64b. the only way to',
            detect these special cases is to explicitly check,',
            the opcodes',
        */
        if (iFmt->SRC0 == REG_SRC_LITERAL || (iFmt->SRC0 == REG_SRC_DPP) ||
            (iFmt->SRC0 == REG_SRC_SWDA) || iFmt->OP == 0x17 ||
            iFmt->OP == 0x18 || iFmt->OP == 0x24 || iFmt->OP == 0x25)
            return true;

        return false;
    }

    void
    Inst_VOP2::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        dis_stream << "v" << instData.VDST << ", ";

        if (writesVCC())
            dis_stream << "vcc, ";

        if ((instData.SRC0 == REG_SRC_LITERAL) ||
            (instData.SRC0 == REG_SRC_DPP) ||
            (instData.SRC0 == REG_SRC_SWDA)) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << _srcLiteral << ", ";
        } else {
            dis_stream << opSelectorToRegSym(instData.SRC0) << ", ";
        }

        // VOP2 instructions have four special opcodes:',
        // V_MADMK_{F16, F32} (0x24, 0x17), and V_MADAK_{F16, F32}',
        // (0x25, 0x18), that are always 64b. the only way to',
        // detect these special cases is to explicitly check,',
        // the opcodes',
        if (instData.OP == 0x17 || instData.OP == 0x18 || instData.OP == 0x24
            || instData.OP == 0x25) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << extData.imm_u32 << ", ";
        }

        dis_stream << std::resetiosflags(std::ios_base::basefield) << "v"
            << instData.VSRC1;

        if (readsVCC())
            dis_stream << ", vcc";

        disassembly = dis_stream.str();
    }

    // --- Inst_VOP1 base class methods ---

    Inst_VOP1::Inst_VOP1(InFmt_VOP1 *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
            if (iFmt->SRC0 == REG_SRC_DPP) {
                setFlag(IsDPP);
            } else if (iFmt->SRC0 == REG_SRC_SWDA) {
                setFlag(IsSDWA);
            }
        } else {
            varSize = 4;
        } // if
    } // Inst_VOP1

    Inst_VOP1::~Inst_VOP1()
    {
    } // ~Inst_VOP1

    void
    Inst_VOP1::initOperandInfo()
    {
        int opNum = 0;
        // Needed because can't take addr of bitfield
        int reg = instData.SRC0;

        if (numSrcRegOperands()) {
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  isScalarReg(reg), isVectorReg(reg), false);
            opNum++;
        }

        if (numDstRegOperands()) {
            reg = instData.VDST;
            /*
              The v_readfirstlane_b32 instruction (op = 2) is a special case
              VOP1 instruction which has a scalar register as the destination.
              (See section 6.6.2 "Special Cases" in the Vega ISA manual)

              Therefore we change the dest op to be scalar reg = true and
              vector reg = false in reserve of all other instructions.
             */
            if (instData.OP == 2) {
                dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                      true, false, false);
            } else {
                dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                      false, true, false);
            }
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOP1::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_VOP1::hasSecondDword(InFmt_VOP1 *iFmt)
    {
        /*
          There are several cases where VOP1 instructions have a second dword:

            1.  SRC0 is a literal.
            2.  SRC0 is being used to add a data parallel primitive (DPP)
            operation to the instruction.
            3.  SRC0 is being used for sub d-word addressing (SDWA) of the
            operands in the instruction.
        */
        if ((iFmt->SRC0 == REG_SRC_LITERAL) || (iFmt->SRC0 == REG_SRC_DPP) ||
            (iFmt->SRC0 == REG_SRC_SWDA))
            return true;

        return false;
    }

    void
    Inst_VOP1::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        dis_stream << "v" << instData.VDST << ", ";

        if ((instData.SRC0 == REG_SRC_LITERAL) ||
            (instData.SRC0 == REG_SRC_DPP) ||
            (instData.SRC0 == REG_SRC_SWDA)) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << _srcLiteral;
        } else {
            dis_stream << opSelectorToRegSym(instData.SRC0);
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_VOPC base class methods ---

    Inst_VOPC::Inst_VOPC(InFmt_VOPC *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(WritesVCC);
        // copy first instruction DWORD
        instData = iFmt[0];
        if (hasSecondDword(iFmt)) {
            // copy second instruction DWORD into union
            extData = ((MachInst)iFmt)[1];
            _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
            varSize = 4 + 4;
            if (iFmt->SRC0 == REG_SRC_DPP) {
                setFlag(IsDPP);
            } else if (iFmt->SRC0 == REG_SRC_SWDA) {
                setFlag(IsSDWA);
            }
        } else {
            varSize = 4;
        } // if
    } // Inst_VOPC

    Inst_VOPC::~Inst_VOPC()
    {
    } // ~Inst_VOPC

    void
    Inst_VOPC::initOperandInfo()
    {
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = instData.SRC0;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(reg), isVectorReg(reg), false);
        opNum++;

        reg = instData.VSRC1;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        assert(writesVCC());
        dstOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), false,
                              true, false, false);

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOPC::instSize() const
    {
        return varSize;
    } // instSize

    bool
    Inst_VOPC::hasSecondDword(InFmt_VOPC *iFmt)
    {
        /*
          There are several cases where VOPC instructions have a second dword:

            1.  SRC0 is a literal.
            2.  SRC0 is being used to add a data parallel primitive (DPP)
            operation to the instruction.
            3.  SRC0 is being used for sub d-word addressing (SDWA) of the
            operands in the instruction.
        */
        if ((iFmt->SRC0 == REG_SRC_LITERAL) || (iFmt->SRC0 == REG_SRC_DPP) ||
            (iFmt->SRC0 == REG_SRC_SWDA))
            return true;

        return false;
    }

    void
    Inst_VOPC::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " vcc, ";

        if ((instData.SRC0 == REG_SRC_LITERAL) ||
            (instData.SRC0 == REG_SRC_DPP) ||
            (instData.SRC0 == REG_SRC_SWDA)) {
            dis_stream << "0x" << std::hex << std::setfill('0') << std::setw(8)
                       << _srcLiteral << ", ";
        } else {
            dis_stream << opSelectorToRegSym(instData.SRC0) << ", ";
        }
        dis_stream << "v" << instData.VSRC1;

        disassembly = dis_stream.str();
    }

    // --- Inst_VINTRP base class methods ---

    Inst_VINTRP::Inst_VINTRP(InFmt_VINTRP *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
    } // Inst_VINTRP

    Inst_VINTRP::~Inst_VINTRP()
    {
    } // ~Inst_VINTRP

    int
    Inst_VINTRP::instSize() const
    {
        return 4;
    } // instSize

    // --- Inst_VOP3A base class methods ---

    Inst_VOP3A::Inst_VOP3A(InFmt_VOP3A *iFmt, const std::string &opcode,
                         bool sgpr_dst)
        : VEGAGPUStaticInst(opcode), sgprDst(sgpr_dst)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_VOP3_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
    } // Inst_VOP3A

    Inst_VOP3A::~Inst_VOP3A()
    {
    } // ~Inst_VOP3A

    void
    Inst_VOP3A::initOperandInfo()
    {
        // Also takes care of bitfield addr issue
        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};

        int opNum = 0;

        int numSrc = numSrcRegOperands() - readsVCC();
        int numDst = numDstRegOperands() - writesVCC() - writesEXEC();

        for (opNum = 0; opNum < numSrc; opNum++) {
            srcOps.emplace_back(srcs[opNum], getOperandSize(opNum), true,
                                  isScalarReg(srcs[opNum]),
                                  isVectorReg(srcs[opNum]), false);
        }

        if (readsVCC()) {
            srcOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), true,
                                  true, false, false);
            opNum++;
        }

        if (numDst) {
            // Needed because can't take addr of bitfield
            int reg = instData.VDST;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  sgprDst, !sgprDst, false);
            opNum++;
        }

        if (writesVCC()) {
            dstOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), false,
                                  true, false, false);
        }

        // Completely ignore if writesEXEC() is true. Instructions which write
        // EXEC do so by writing to a wavefront register rather than SGPRs.
        // The SGPR index values for EXEC are used as aliases to the wavefront
        // register in gem5.
        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDst);
    }

    int
    Inst_VOP3A::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_VOP3A::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        int num_regs = 0;

        if (getOperandSize(getNumOperands() - 1) > 4) {
            num_regs = getOperandSize(getNumOperands() - 1) / 4;
            if (sgprDst)
                dis_stream << "s[";
            else
                dis_stream << "v[";
            dis_stream << instData.VDST << ":" << instData.VDST +
                          num_regs - 1 << "], ";
        } else {
            if (sgprDst)
                dis_stream << "s";
            else
                dis_stream << "v";
            dis_stream << instData.VDST << ", ";
        }

        num_regs = getOperandSize(0) / 4;

        if (extData.NEG & 0x1) {
            dis_stream << "-" << opSelectorToRegSym(extData.SRC0, num_regs);
        } else {
            dis_stream << opSelectorToRegSym(extData.SRC0, num_regs);
        }

        if (numSrcRegOperands() > 1) {
            num_regs = getOperandSize(1) / 4;

            if (extData.NEG & 0x2) {
                dis_stream << ", -"
                    << opSelectorToRegSym(extData.SRC1, num_regs);
            } else {
                dis_stream << ", "
                    << opSelectorToRegSym(extData.SRC1, num_regs);
            }
        }

        if (numSrcRegOperands() > 2) {
            num_regs = getOperandSize(2) / 4;

            if (extData.NEG & 0x4) {
                dis_stream << ", -"
                    << opSelectorToRegSym(extData.SRC2, num_regs);
            } else {
                dis_stream << ", "
                    << opSelectorToRegSym(extData.SRC2, num_regs);
            }
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_VOP3B base class methods ---

    Inst_VOP3B::Inst_VOP3B(InFmt_VOP3B *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_VOP3_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
    } // Inst_VOP3B

    Inst_VOP3B::~Inst_VOP3B()
    {
    } // ~Inst_VOP3B

    void
    Inst_VOP3B::initOperandInfo()
    {
        // Also takes care of bitfield addr issue
        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};

        int opNum = 0;

        int numSrc = numSrcRegOperands() - readsVCC();
        int numDst = numDstRegOperands() - writesVCC();

        for (opNum = 0; opNum < numSrc; opNum++) {
            srcOps.emplace_back(srcs[opNum], getOperandSize(opNum), true,
                                  isScalarReg(srcs[opNum]),
                                  isVectorReg(srcs[opNum]), false);
        }

        if (readsVCC()) {
            srcOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), true,
                                  true, false, false);
            opNum++;
        }

        if (numDst) {
            // Needed because can't take addr of bitfield
            int reg = instData.VDST;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
            opNum++;
        }

        if (writesVCC()) {
            dstOps.emplace_back(REG_VCC_LO, getOperandSize(opNum), false,
                                  true, false, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOP3B::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_VOP3B::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        dis_stream << "v" << instData.VDST << ", ";

        if (numDstRegOperands() == 2) {
            if (getOperandSize(getNumOperands() - 1) > 4) {
                int num_regs = getOperandSize(getNumOperands() - 1) / 4;
                dis_stream << opSelectorToRegSym(instData.SDST, num_regs)
                    << ", ";
            } else {
                dis_stream << opSelectorToRegSym(instData.SDST) << ", ";
            }
        }

        if (extData.NEG & 0x1) {
            dis_stream << "-" << opSelectorToRegSym(extData.SRC0) << ", ";
        } else {
            dis_stream << opSelectorToRegSym(extData.SRC0) << ", ";
        }

        if (extData.NEG & 0x2) {
            dis_stream << "-" << opSelectorToRegSym(extData.SRC1);
        } else {
            dis_stream << opSelectorToRegSym(extData.SRC1);
        }

        if (numSrcRegOperands() == 3) {
            if (extData.NEG & 0x4) {
                dis_stream << ", -" << opSelectorToRegSym(extData.SRC2);
            } else {
                dis_stream << ", " << opSelectorToRegSym(extData.SRC2);
            }
        }

        if (readsVCC())
            dis_stream << ", vcc";

        disassembly = dis_stream.str();
    }

    // --- Inst_VOP3P base class methods ---

    Inst_VOP3P::Inst_VOP3P(InFmt_VOP3P *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_VOP3P_1 *)iFmt)[1];
    } // Inst_VOP3P

    Inst_VOP3P::~Inst_VOP3P()
    {
    } // ~Inst_VOP3P

    void
    Inst_VOP3P::initOperandInfo()
    {
        // Also takes care of bitfield addr issue
        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};

        int opNum = 0;

        int numSrc = numSrcRegOperands();

        for (opNum = 0; opNum < numSrc; opNum++) {
            srcOps.emplace_back(srcs[opNum], getOperandSize(opNum), true,
                                  isScalarReg(srcs[opNum]),
                                  isVectorReg(srcs[opNum]), false);
        }

        // There is always one dest
        // Needed because can't take addr of bitfield
        int reg = instData.VDST;
        dstOps.emplace_back(reg, getOperandSize(opNum), false,
                              false, true, false);
        opNum++;

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOP3P::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_VOP3P::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        // There is always a dest and the index is after the src operands
        // The output size much be a multiple of dword size
        int dst_size = getOperandSize(numSrcRegOperands());

        dis_stream << opSelectorToRegSym(instData.VDST + 0x100, dst_size / 4);

        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};
        for (int opnum = 0; opnum < numSrcRegOperands(); opnum++) {
            int num_regs = getOperandSize(opnum) / 4;
            dis_stream << ", " << opSelectorToRegSym(srcs[opnum], num_regs);
        }

        // Print op_sel only if one is non-zero
        if (instData.OPSEL) {
            int opsel = instData.OPSEL;

            dis_stream << " op_sel:[" << bits(opsel, 0, 0) << ","
                    << bits(opsel, 1, 1) << "," << bits(opsel, 2, 2) << "]";
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_VOP3P_MAI base class methods ---

    Inst_VOP3P_MAI::Inst_VOP3P_MAI(InFmt_VOP3P_MAI *iFmt,
                                   const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_VOP3P_MAI_1 *)iFmt)[1];
    } // Inst_VOP3P_MAI

    Inst_VOP3P_MAI::~Inst_VOP3P_MAI()
    {
    } // ~Inst_VOP3P_MAI

    void
    Inst_VOP3P_MAI::initOperandInfo()
    {
        // Also takes care of bitfield addr issue
        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};

        int opNum = 0;

        int numSrc = numSrcRegOperands();

        for (opNum = 0; opNum < numSrc; opNum++) {
            srcOps.emplace_back(srcs[opNum], getOperandSize(opNum), true,
                                  isScalarReg(srcs[opNum]),
                                  isVectorReg(srcs[opNum]), false);
        }

        // There is always one dest
        // Needed because can't take addr of bitfield
        int reg = instData.VDST;
        dstOps.emplace_back(reg, getOperandSize(opNum), false,
                              false, true, false);
        opNum++;

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_VOP3P_MAI::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_VOP3P_MAI::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        // There is always a dest and the index is after the src operands
        // The output size much be a multiple of dword size
        int dst_size = getOperandSize(numSrcRegOperands());

        // opSelectorToRegSym handles formating for us. VDST is always VGPR
        // so only the last 8 bits are used. This adds the implicit 9th bit
        // which is 1 for VGPRs as VGPR op nums are from 256-255.
        int dst_opnum = instData.VDST + 0x100;

        dis_stream << opSelectorToRegSym(dst_opnum, dst_size / 4);

        unsigned int srcs[3] = {extData.SRC0, extData.SRC1, extData.SRC2};
        for (int opnum = 0; opnum < numSrcRegOperands(); opnum++) {
            int num_regs = getOperandSize(opnum) / 4;
            dis_stream << ", " << opSelectorToRegSym(srcs[opnum], num_regs);
        }

        disassembly = dis_stream.str();
    }

    // --- Inst_DS base class methods ---

    Inst_DS::Inst_DS(InFmt_DS *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        setFlag(GroupSegment);

        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_DS_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
    } // Inst_DS

    Inst_DS::~Inst_DS()
    {
    } // ~Inst_DS

    void
    Inst_DS::initOperandInfo()
    {
        unsigned int srcs[3] = {extData.ADDR, extData.DATA0, extData.DATA1};

        int opIdx = 0;

        for (opIdx = 0; opIdx < numSrcRegOperands(); opIdx++){
            srcOps.emplace_back(srcs[opIdx], getOperandSize(opIdx), true,
                                  false, true, false);
        }

        if (numDstRegOperands()) {
            // Needed because can't take addr of bitfield
            int reg = extData.VDST;
            dstOps.emplace_back(reg, getOperandSize(opIdx), false,
                                  false, true, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_DS::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_DS::generateDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        if (numDstRegOperands())
            dis_stream << "v" << extData.VDST << ", ";

        dis_stream << "v" << extData.ADDR;

        if (numSrcRegOperands() > 1)
            dis_stream << ", v" << extData.DATA0;

        if (numSrcRegOperands() > 2)
            dis_stream << ", v" << extData.DATA1;

        uint16_t offset = 0;

        if (instData.OFFSET1) {
            offset += instData.OFFSET1;
            offset <<= 8;
        }

        if (instData.OFFSET0)
            offset += instData.OFFSET0;

        if (offset)
            dis_stream << " offset:" << offset;

        disassembly = dis_stream.str();
    }

    // --- Inst_MUBUF base class methods ---

    Inst_MUBUF::Inst_MUBUF(InFmt_MUBUF *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_MUBUF_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);

        if (instData.GLC)
            setFlag(GloballyCoherent);

        if (instData.SLC)
            setFlag(SystemCoherent);
    } // Inst_MUBUF

    Inst_MUBUF::~Inst_MUBUF()
    {
    } // ~Inst_MUBUF

    void
    Inst_MUBUF::initOperandInfo()
    {
        // Currently there are three formats:
        // 0 src + 0 dst
        // 3 src + 1 dst
        // 4 src + 0 dst
        int opNum = 0;

        // Needed because can't take addr of bitfield;
        int reg = 0;

        if (numSrcRegOperands()) {
            if (numSrcRegOperands() == getNumOperands()) {
                reg = extData.VDATA;
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      false, true, false);
                opNum++;
            }

            reg = extData.VADDR;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, true, false);
            opNum++;

            reg = extData.SRSRC;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  isScalarReg(reg), false, false);
            opNum++;

            reg = extData.SOFFSET;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  isScalarReg(reg), false, false);
            opNum++;
        }

        // extData.VDATA moves in the reg list depending on the instruction
        if (numDstRegOperands()) {
            reg = extData.VDATA;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_MUBUF::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_MUBUF::generateDisassembly()
    {
        // SRSRC is always in units of 4 SGPRs
        int srsrc_val = extData.SRSRC * 4;
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";
        dis_stream << "v" << extData.VDATA << ", v" << extData.VADDR << ", ";
        dis_stream << "s[" << srsrc_val << ":"
                   << srsrc_val + 3 << "], ";
        dis_stream << "s" << extData.SOFFSET;

        if (instData.OFFSET)
            dis_stream << ", offset:" << instData.OFFSET;

        disassembly = dis_stream.str();
    }

    // --- Inst_MTBUF base class methods ---

    Inst_MTBUF::Inst_MTBUF(InFmt_MTBUF *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_MTBUF_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);

        if (instData.GLC)
            setFlag(GloballyCoherent);

        if (extData.SLC)
            setFlag(SystemCoherent);
    } // Inst_MTBUF

    Inst_MTBUF::~Inst_MTBUF()
    {
    } // ~Inst_MTBUF

    void
    Inst_MTBUF::initOperandInfo()
    {
        // Currently there are two formats:
        // 3 src + 1 dst
        // 4 src + 0 dst
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = 0;

        if (numSrcRegOperands() == getNumOperands()) {
            reg = extData.VDATA;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, true, false);
            opNum++;
        }

        reg = extData.VADDR;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        reg = extData.SRSRC;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(reg), false, false);
        opNum++;

        reg = extData.SOFFSET;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(reg), false, false);
        opNum++;

        // extData.VDATA moves in the reg list depending on the instruction
        if (numDstRegOperands()) {
            reg = extData.VDATA;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_MTBUF::instSize() const
    {
        return 8;
    } // instSize

    // --- Inst_MIMG base class methods ---

    Inst_MIMG::Inst_MIMG(InFmt_MIMG *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_MIMG_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);

        if (instData.GLC)
            setFlag(GloballyCoherent);

        if (instData.SLC)
            setFlag(SystemCoherent);
    } // Inst_MIMG

    Inst_MIMG::~Inst_MIMG()
    {
    } // ~Inst_MIMG

    void
    Inst_MIMG::initOperandInfo()
    {
        // Three formats:
        // 1 dst + 2 src : s,s,d
        // 0 dst + 3 src : s,s,s
        // 1 dst + 3 src : s,s,s,d
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = 0;

        if (numSrcRegOperands() == getNumOperands()) {
            reg = extData.VDATA;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, true, false);
            opNum++;
        }

        reg = extData.VADDR;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        reg = extData.SRSRC;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              isScalarReg(reg), false, false);
        opNum++;

        if (getNumOperands() == 4) {
            reg = extData.SSAMP;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  isScalarReg(reg), false, false);
            opNum++;
        }

        // extData.VDATA moves in the reg list depending on the instruction
        if (numDstRegOperands()) {
            reg = extData.VDATA;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_MIMG::instSize() const
    {
        return 8;
    } // instSize

    // --- Inst_EXP base class methods ---

    Inst_EXP::Inst_EXP(InFmt_EXP *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_EXP_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);
    } // Inst_EXP

    Inst_EXP::~Inst_EXP()
    {
    } // ~Inst_EXP

    void
    Inst_EXP::initOperandInfo()
    {
        // Only 1 instruction, 1 format: 1 dst + 4 src
        int opNum = 0;

        // Avoids taking addr of bitfield
        unsigned int srcs[4] = {extData.VSRC0, extData.VSRC1,
                                extData.VSRC2, extData.VSRC3};

        for (opNum = 0; opNum < 4; opNum++) {
            srcOps.emplace_back(srcs[opNum], getOperandSize(opNum), true,
                                  false, true, false);
        }

        //TODO: Add the dst operand, don't know what it is right now
    }

    int
    Inst_EXP::instSize() const
    {
        return 8;
    } // instSize

    // --- Inst_FLAT base class methods ---

    Inst_FLAT::Inst_FLAT(InFmt_FLAT *iFmt, const std::string &opcode)
        : VEGAGPUStaticInst(opcode)
    {
        // The SEG field specifies FLAT(0) SCRATCH(1) or GLOBAL(2)
        if (iFmt->SEG == 0) {
            setFlag(Flat);
        } else if (iFmt->SEG == 1) {
            setFlag(FlatScratch);
        } else if (iFmt->SEG == 2) {
            setFlag(FlatGlobal);
        } else {
            panic("Unknown flat segment: %d\n", iFmt->SEG);
        }

        // copy first instruction DWORD
        instData = iFmt[0];
        // copy second instruction DWORD
        extData = ((InFmt_FLAT_1 *)iFmt)[1];
        _srcLiteral = *reinterpret_cast<uint32_t*>(&iFmt[1]);

        if (instData.GLC)
            setFlag(GloballyCoherent);

        if (instData.SLC)
            setFlag(SystemCoherent);
    } // Inst_FLAT

    Inst_FLAT::~Inst_FLAT()
    {
    } // ~Inst_FLAT

    void
    Inst_FLAT::initOperandInfo()
    {
        // One of the flat subtypes should be specified via flags
        assert(isFlat() ^ isFlatGlobal() ^ isFlatScratch());

        if (isFlat()) {
            initFlatOperandInfo();
        } else if (isFlatGlobal() || isFlatScratch()) {
            initGlobalScratchOperandInfo();
        } else {
            panic("Unknown flat subtype!\n");
        }
    }

    void
    Inst_FLAT::initFlatOperandInfo()
    {
        //3 formats:
        // 1 dst + 1 src (load)
        // 0 dst + 2 src (store)
        // 1 dst + 2 src (atomic)
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = 0;

        if (getNumOperands() > 2)
            assert(isAtomic());

        reg = extData.ADDR;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        if (numSrcRegOperands() == 2) {
            reg = extData.DATA;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, true, false);
            opNum++;
        }

        if (numDstRegOperands()) {
            reg = extData.VDST;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
        }

        assert(srcOps.size() == numSrcRegOperands());
        assert(dstOps.size() == numDstRegOperands());
    }

    void
    Inst_FLAT::initGlobalScratchOperandInfo()
    {
        //3 formats:
        // 1 dst + 2 src (load)
        // 0 dst + 3 src (store)
        // 1 dst + 3 src (atomic)
        int opNum = 0;

        // Needed because can't take addr of bitfield
        int reg = 0;

        if (getNumOperands() > 3)
            assert(isAtomic());

        reg = extData.ADDR;
        srcOps.emplace_back(reg, getOperandSize(opNum), true,
                              false, true, false);
        opNum++;

        if (numSrcRegOperands() == 2) {
            reg = extData.SADDR;
            // 0x7f (off) means the sgpr is not used. Don't read it
            if (reg != 0x7f) {
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      true, false, false);
            }
            opNum++;
        }

        if (numSrcRegOperands() == 3) {
            reg = extData.DATA;
            srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                  false, true, false);
            opNum++;

            reg = extData.SADDR;
            // 0x7f (off) means the sgpr is not used. Don't read it
            if (reg != 0x7f) {
                srcOps.emplace_back(reg, getOperandSize(opNum), true,
                                      true, false, false);
            }
            opNum++;
        }

        if (numDstRegOperands()) {
            reg = extData.VDST;
            dstOps.emplace_back(reg, getOperandSize(opNum), false,
                                  false, true, false);
        }

        reg = extData.SADDR;
        if (reg != 0x7f) {
            assert(srcOps.size() == numSrcRegOperands());
        } else {
            assert(srcOps.size() == numSrcRegOperands() - 1);
        }
        assert(dstOps.size() == numDstRegOperands());
    }

    int
    Inst_FLAT::instSize() const
    {
        return 8;
    } // instSize

    void
    Inst_FLAT::generateDisassembly()
    {
        // One of the flat subtypes should be specified via flags
        assert(isFlat() ^ isFlatGlobal() ^ isFlatScratch());

        if (isFlatGlobal() || isFlatScratch()) {
            generateGlobalScratchDisassembly();
        } else if (isFlat()) {
            generateFlatDisassembly();
        } else {
            panic("Unknown flat subtype!\n");
        }
    }

    void
    Inst_FLAT::generateFlatDisassembly()
    {
        std::stringstream dis_stream;
        dis_stream << _opcode << " ";

        if (isLoad() || isAtomic()) {
            int dst_size = getOperandSize(numSrcRegOperands()) / 4;
            dis_stream << opSelectorToRegSym(extData.VDST + 0x100, dst_size)
                       << ", ";
        }

        dis_stream << opSelectorToRegSym(extData.ADDR + 0x100, 2);

        if (isStore() || isAtomic()) {
            int src_size = getOperandSize(1) / 4;
            dis_stream << ", "
                << opSelectorToRegSym(extData.DATA + 0x100, src_size);
        }

        disassembly = dis_stream.str();
    }

    void
    Inst_FLAT::generateGlobalScratchDisassembly()
    {
        // Replace flat_ with global_ in assembly string
        std::string global_opcode = _opcode;
        if (isFlatGlobal()) {
            global_opcode.replace(0, 4, "global");
        } else {
            assert(isFlatScratch());
            global_opcode.replace(0, 4, "scratch");
        }

        std::stringstream dis_stream;
        dis_stream << global_opcode << " ";

        if (isLoad() || isAtomic()) {
            // dest is the first operand after all the src operands
            int dst_size = getOperandSize(numSrcRegOperands()) / 4;
            dis_stream << opSelectorToRegSym(extData.VDST + 0x100, dst_size)
                       << ", ";
        }

        if (extData.SADDR == 0x7f) {
            dis_stream << opSelectorToRegSym(extData.ADDR + 0x100, 2);
        } else {
            dis_stream << opSelectorToRegSym(extData.ADDR + 0x100, 1);
        }

        if (isStore() || isAtomic()) {
            int src_size = getOperandSize(1) / 4;
            dis_stream << ", "
                << opSelectorToRegSym(extData.DATA + 0x100, src_size);
        }

        if (extData.SADDR == 0x7f) {
            dis_stream << ", off";
        } else {
            dis_stream << ", " << opSelectorToRegSym(extData.SADDR, 2);
        }

        if (instData.OFFSET) {
            dis_stream << " offset:" << instData.OFFSET;
        }

        if (instData.GLC) {
            dis_stream << " glc";
        }

        disassembly = dis_stream.str();
    }
} // namespace VegaISA
} // namespace gem5
