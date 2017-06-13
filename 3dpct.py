#!/usr/bin/python
# coding=utf-8
#
# 3dpct.py by Florian Schiessl (3.12.2013)
#
# 3d printer control toolchain
#
# This script provides simple communication with a reprap machine.
#
# Usage:
# use -h option ;)
#
import serial, os, sys, re, argparse, string, signal

class gparser:
    def __init__(self):
        # Matches G-Code comments
        self.re_comments = re.compile('\s*;.*$')
        # Matches empty lines
        self.re_empty = re.compile('^\s*$')
        # Matches comment-only lines and BOM
        self.re_comment_only = re.compile('(^\s*;.*$)|(\xef\xbb\xbf*)')
        self.do_checksum = True
        self.parsed = []

    def readfile(self,fname):
        fcontent = []
        if fname == "-":
            fh = sys.stdin
        else:
            fh = open(fname)
        for line in fh:
            fcontent.append(line.rstrip())
        fh.close
        self.fcontent = fcontent

    def checksum(self,line):
        cs = 0
        for i in range(0,len(line)):
            cs ^= ord(line[i]) & 0xff
        cs &= 0xff
        return str(cs)

    def csline(self,line):
        return line+"*"+self.checksum(line)
    
    def prepare_checksum(self):
        self.parsed = []
        return self.csline("M110 N0")
    
    def parse_file(self):
        if self.do_checksum:
            self.prepare_checksum()
        for line in self.fcontent:
            self.parse(line)
        
    def parse(self, line):
        if not self.re_empty.match(line) and not self.re_comment_only.match(line):
            line = self.re_comments.sub("",line)
            if self.do_checksum:
                line = "N"+str(len(self.parsed)+1)+" "+line
                line = self.csline(line)
            self.parsed.append(line)
            return line
        return ""

    def get_parsed(self):
        return self.parsed

    def dump_parsed(self):
        for i in self.parsed:
            print i

class dddprinter:
    def __init__(self):
        self.parser = gparser()
        # Matches Emergency Condition
        self.re_emergency = re.compile('!!')
        # Matches resend query with (optional leading n)
        self.re_resend = re.compile('(^rs [Nn]?)|(^Resend:)')
        # Matches lines which should be ignored
        self.re_ignore = re.compile('(^echo:)|(^[Mm]arlin)|(^start)|(^Error:checksum)|(^T:)')
        self.max_resends = 10
        self.resend_counter = 0
        self.currentln = 1
        self.silent = False # output Printer communication
        self.dir_mark = True # Show direction marks
        self.gcode = [""]

    def loadgcodestring(self,gcodestr):
        self.loadgcode = gcodestr.split(gcodestr, "\n")

    def loadgcode(self,gcode):
        self.gcode = [""] # For correct line Numbering
        self.gcode.extend(gcode)

    def connect(self,tty,baud):
        self.ser = serial.Serial(tty, baud, timeout=1)
        #self.cswrite("M110 N0") # Reset Line Counter

    def cswrite(self,line):
        self.write(parser.csline(line))

    def ldm(self,line):
        if self.silent: return
        if self.dir_mark: print "<~: "+line
        else: print line

    def rdm(self,line):
        if self.silent: return
        if self.dir_mark: print "~>: "+line
        else: print line

    def rprpt(self):
        if self.silent: return ""
        if self.dir_mark: return "<-: "
        else: return ""

    def write(self,line):
        self.ldm(line)
        self.ser.write(line+"\n")

    def read(self):
        result = self.ser.readline().rstrip()
        self.rdm(result)
        return result

    def read_flush(self):
        result = self.read()
        while not result == "":
            result = self.read()
        print "--- EOF ---"

    def resend(self,linenumber):
        self.write(self.gcode[linenumber])
        if self.resend_counter <= self.max_resends:
            self.waitforok()
            self.currentln = linenumber # Re-Send all after Checksum-Error
        else:
            self.panic("too many resends!")

    def waitforok(self):
        result = self.read().rstrip()
        while (len(result) == 0 or
                self.re_ignore.match(result) or
                parser.re_empty.match(result)):
            result = self.read().rstrip() # Ignore empty lines, unuseful infos, 0-lenght
        if self.re_emergency.match(result):
            # Emergency
            self.panic("received EMERGENCY CONDITION!")
        elif self.re_resend.match(result):
            # Printer queried a resend
            self.read_flush()
            result = self.re_resend.sub("",result) # removing request
            self.resend(int(result))
        elif result == "ok":
            # ok
            self.resend_counter = 0
        else:
            self.panic("UNKNOWN:"+result+":"+str(len(result)))
        return


    def _print(self):
        while self.currentln < len(self.gcode):
            self.write(self.gcode[self.currentln])
            self.waitforok()
            self.currentln += 1
        print "Print successfull :D"
        print "programm succeeded."
        sys.exit(0)

    def panic(self,message):
        print message
        print "flushing input:"
        self.read_flush()
        print "programm stopped."
        sys.exit(1)

    def start_cli(self):
        if self.parser.do_checksum:
            self.write(self.parser.prepare_checksum())
            self.waitforok()
        while(1):
            output = self.parser.parse(raw_input(self.rprpt()))
            if not output == "":
                self.write(output)
                self.waitforok()
            


if __name__ == "__main__":
    parser = gparser()
    printer = dddprinter()
    argp = argparse.ArgumentParser(
        description="3dpct - a 3d printer control toolchain",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argp.add_argument(
        "-f", "--file",
        metavar="FILE",
        action="append",
        default=argparse.SUPPRESS,
        help="load gcode from given file name or use '-' for STDIN",
        nargs="?")
    argp.add_argument(
        "-o", "--output",
        action='store_true',
        default=argparse.SUPPRESS,
        help="output filtered gcode to STDOUT")
    argp.add_argument(
        "-p","--print",
        action='store_true',
        default=argparse.SUPPRESS,
        help="use 3d printer to print gcode")
    argp.add_argument(
        "-c", "--cli",
        action='store_true',
        default=argparse.SUPPRESS,
        help="start a cli for manual printer control using gcodes")
    argp.add_argument(
        "-n","--no-direction-mark",
        action='store_true',
        default=argparse.SUPPRESS,
        help="don't show direction marks and prompt (eg: <~: ,~>: ,<-: )")
    argp.add_argument(
        "-e", "--execute",
        action='store',
        default=argparse.SUPPRESS,
        nargs=argparse.REMAINDER,
        help="execute a single gcode line (must be last argument)")
    argp.add_argument(
        "--no-checksum",
        action='store_true',
        default=argparse.SUPPRESS,
        help="don't generate line numbers and checksums")
    argp.add_argument(
        "--silent",
        action="store_true",
        default=argparse.SUPPRESS,
        help="don't output communication while printing")
    argp.add_argument(
        "-d","--device",
        metavar="DEVICE",
        default="/dev/ttyUSB0",
        help="the device to use for printing",
        nargs="?")
    argp.add_argument(
        "-b","--baud",
        default=250000,
        help="the baudrate to use on device",
        nargs="?",
        type=int)
    args = vars(argp.parse_args())

    # Catching Signals
    def signal_handler(signal, frame):
        print ""
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    # parsing options
    done = False
    if 'no_checksum' in args:
        parser.do_checksum = False
        printer.parser.do_checksum = False
    if 'no_direction_mark' in args:
        printer.dir_mark = False
    if 'silent' in args:
        printer.silent = True
    if 'file' in args:
        parser.readfile(args['file'][0])
        parser.parse_file()
        if 'output' in args:
            parser.dump_parsed()
            done = True
        if 'print' in args:
            print "Using device "+args['device']+" with "+str(args['baud'])+" Baud."
            printer.connect(args['device'], args['baud'])
            if printer.parser.do_checksum:
                printer.write(printer.parser.prepare_checksum())
                printer.waitforok()
            printer.loadgcode(parser.get_parsed())
            printer._print()
            done = True
    elif 'cli' in args:
        printer.connect(args['device'], args['baud'])
        printer.start_cli()
        done = True
    elif 'execute' in args:
        printer.connect(args['device'], args['baud'])
        if printer.parser.do_checksum:
            printer.write(printer.parser.prepare_checksum())
            printer.waitforok()
        printer.write(printer.parser.parse(" ".join(args['execute'])))
        printer.waitforok()
        done = True

    if not done:
        argp.print_help()
