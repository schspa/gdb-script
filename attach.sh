#!/bin/bash
# simplified version of ps; output in the form
# <pid> <procname>
function qpid() {
    local prepend=''
    local append=''
    if [ "$1" = "--exact" ]; then
        prepend=' '
        append='$'
        shift
    elif [ "$1" = "--help" -o "$1" = "-h" ]; then
        echo "usage: qpid [[--exact] <process name|pid>"
        return 255
    fi

    local EXE="$1"
    if [ "$EXE" ] ; then
        qpid | \grep "$prepend$EXE$append"
    else
        adb shell ps \
            | tr -d '\r' \
            | sed -e 1d -e 's/^[^ ]* *\([0-9]*\).* \([^ ]*\)$/\1 \2/'
    fi
}

# Read the ELF header from /proc/$PID/exe to determine if the process is
# 64-bit.
function is64bit()
{
    local PID="$1"
    if [ "$PID" ] ; then
        if [[ "$(adb shell cat /proc/$PID/exe | xxd -l 1 -s 4 -ps)" -eq "02" ]] ; then
            echo "64"
        else
            echo ""
        fi
    else
        echo ""
    fi
}

pid=$(qpid $1 | awk -F " " '{print $1}')
bits=$(is64bit "$pid")
echo "attaching to process $pid abi: $bits"

GDBSERVER=~/work/code/aosp/prebuilts/misc/android-arm${bits}/gdbserver${bits}/gdbserver${bits}
if [ "$ANDROID_BUILD_TOP"x != ""x ]; then
	GDBSERVER=${ANDROID_BUILD_TOP}/prebuilts/misc/android-arm${bits}/gdbserver${bits}/gdbserver${bits}
fi

if [ ! -f $GDBSERVER ]; then
	echo "gdbserver $GDBSERVER not exits"
	exit -1
fi

adb wait-for-device root
adb shell "setenforce 0"
adb push $GDBSERVER /data/gdbserver${bits}
adb shell "chmod 777 /data/gdbserver${bits}"
adb forward tcp:8888 tcp:8888

aaa=$(adb shell "cat /proc/${pid}/cmdline")
symbos_dir=$2
echo "symbols_dir=$symbos_dir"
exefile=$(adb shell "cat /proc/${pid}/cmdline")

exec_file=$symbos_dir$exefile

if [ ! -f $exec_file ]; then
	echo "con't find execute file $exec_file"
	exit -2
fi
screen -X -S gdb quit
screen -AdmS gdb
screen -S gdb -X stuff "adb shell \"/data/gdbserver${bits} :8888 --attach $pid\"\n"
sleep 2
echo "debugging $exec_file"
GDBBIN=~/work/code/aosp/prebuilts/gdb/linux-x86/bin/gdb
if [ "$ANDROID_BUILD_TOP"x != ""x ]; then
	GDBBIN=${ANDROID_BUILD_TOP}/prebuilts/gdb/linux-x86/bin/gdb
fi
${GDBBIN} $exec_file -ex "set sysroot $symbos_dir" -ex "target remote :8888"
screen -X -S gdb quit
