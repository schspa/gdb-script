#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   dump-dtb.py --- dump dtb
#
#   Copyright (C) 2023, Schspa, all rights reserved.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import struct

file_path = os.path.abspath(os.path.dirname(__file__))
ms = None;

class DebuggerService():
    """Debugger Service which support both gdb & ds5.
    """

    def __init__(self):
        try:
            from arm_ds.debugger_v1 import Debugger
            from arm_ds.debugger_v1 import DebugException
            # Debugger object for accessing the debugger
            print("Using DS5 as backend")
            # sw/ide/plugins/com.arm.debug.interpreter.jython.api_2020.11.0.20201112_191846/
            # https://developer.arm.com/documentation/dui0446/j/BABIAEDF

            debugger = Debugger()

            # Initialisation commands
            ec = debugger.getExecutionContext(0)
            ec.getExecutionService().stop()
            ec.getExecutionService().waitForStop()
            ms = ec.getMemoryService();
            self.readmem = ms.read
            self.backend = 'ds5'
        except BaseException as e:
            print("Using GDB as backend")
            try:
                inferior = gdb.selected_inferior()
            except RuntimeError:
                return
            if not inferior or not inferior.is_valid():
                return

            self.readmem = inferior.read_memory
            self.backend = 'gdb'

    def debugger_backend(self):
        return self.backend

    def dump_dtb(self, dtb_addr, file_path):
        print("Dump dtb from 0x%08x to %s" % (dtb_addr, file_path))
        data = self.readmem(dtb_addr, 12)
        magic, totalsize, version = struct.unpack('>III', data)

        print("magic: 0x%08x, totalsize: 0x%08x, version: 0x%08x" % (magic, totalsize, version))
        if magic != 0xd00dfeed:
            return -1

        dtbblob = self.readmem(dtb_addr, totalsize)
        with open(file_path, 'wb') as f:
            f.write(dtbblob)
        print("dtb %s was generated" % (file_path))


ds = DebuggerService()

if ds.debugger_backend() == 'ds5':

    if __name__ == '__main__':
        if len(sys.argv) < 3:
            print("Usage: source %s <address for dtb with base 16> <file_path>" % (sys.argv[0]))
            exit(-1)

        dtb_addr = int(sys.argv[1], 16)
        ds.dump_dtb(dtb_addr, sys.argv[2])

if ds.debugger_backend() == 'gdb':

    import gdb
    class Load_dtb_dump_command(gdb.Command):
        "Load Linux Kernel init text from vmlinux"

        def __init__(self):
            super(Load_dtb_dump_command,
                  self).__init__("dtb_dump", gdb.COMMAND_SUPPORT,
                                 gdb.COMPLETE_EXPRESSION, True)

        def invoke(self, arg, from_tty):
            argv = gdb.string_to_argv(arg)
            if len(argv) != 2:
                raise gdb.GdbError("load-linux-init takes two argument")

            dtb_addr = int(str(gdb.parse_and_eval(argv[0])))
            dump_path = str(argv[1])
            ds.dump_dtb(dtb_addr, dump_path)

    Load_dtb_dump_command()
    pass
