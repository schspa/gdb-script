#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   load-linux-init.py --- Load linux kernel init section
#
#   Copyright (C) 2020, schspa, all rights reserved.
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
import re
import gdb
from subprocess import check_output, CalledProcessError


class LoadLinuxKernelInitCommand(gdb.Command):
    "Load Linux Kernel init text from vmlinux"

    def __init__(self):
        super(LoadLinuxKernelInitCommand,
              self).__init__("load-linux-init", gdb.COMMAND_SUPPORT,
                             gdb.COMPLETE_EXPRESSION, True)

    def get_load_address(self, path, section):
        '''
		[Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
		[ 0]                   NULL            0000000000000000 000000 000000 00      0   0  0
		[ 1] .head.text        PROGBITS        ffffff8008080000 010000 001000 00  AX  0   0 4096
		[ 2] .text             PROGBITS        ffffff8008081000 011000 5ee1b0 00  AX  0   0 2048
	'''

        ELF_PATTERN = re.compile(r"^[\s]*\[(?P<NUM>[0-9 ]+)\]" +
                                 r"[\s]+(?P<NAME>[\S]+)" +
                                 r"[\s]+(?P<Type>[\S]+)" +
                                 r"[\s]+(?P<Address>[\S]+)" +
                                 r"[\s]+(?P<Off>[\S]+)" +
                                 r"[\s]+(?P<Size>[\S]+)" +
                                 r"[\s]+(?P<ES>[\S]+)" +
                                 r"[\s]+(?P<Flg>[\S]+)")

        command = r"readelf -WS " + path + r"| grep -E '[[:space:]]+'" + section
        output = check_output([command], shell=True).decode("utf-8")
        obj = re.search(ELF_PATTERN, output)
        if obj is not None:
            load_addr = int(obj['Address'], 16)
            return load_addr

    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 2:
            raise gdb.GdbError("load-linux-init takes two argument")

        load_addr = int(str(gdb.parse_and_eval(argv[1])))
        print("Loading linux init head to 0x%016x" % (load_addr))
        head_init_addr = self.get_load_address(argv[0], ".head.text")
        print("Original linux text address at 0x%016x" % (head_init_addr))
        offset = head_init_addr - load_addr
        text_addr = self.get_load_address(argv[0], ".text") - offset
        init_text_addr = self.get_load_address(argv[0], ".init.text") - offset

        command = "add-symbol-file {:s} 0x{:x} -s .head.text 0x{:x} -s .init.text 0x{:x}".format(
            argv[0], text_addr, load_addr, init_text_addr)
        print("load linux image to physical address with command {:s}".format(
            command))
        gdb.execute(command)


LoadLinuxKernelInitCommand()

# Local Variables:
# indent-tabs-mode: t
# tab-width: 8
# End:
