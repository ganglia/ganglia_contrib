#!/usr/bin/python
"""Tail a file, reopening it if it gets rotated"""

import time, os, sys, glob


class Tail(object):
    def __init__(self, filename, start_pos=0):
        self.fp = file(filename)
        self.filename = filename

        if start_pos < 0:
            self.fp.seek(-start_pos-1, 2)
            self.pos = self.fp.tell()
        else:
            self.fp.seek(start_pos)
            self.pos = start_pos

    def __iter__(self):
        """Return next line.  This function will sleep until there *is* a
        next line.  Works over log rotation."""
        counter = 0
        while True:
            line = self.next()
            if line is None:
                counter += 1
                if counter >= 5:
                    counter = 0
                    self.check_inode()
                time.sleep(1.0)
            else:
                yield line

    def check_inode(self):
        """check to see if the filename we expect to tail has the same
        inode as our currently open file.  This catches log rotation"""
        inode = os.stat(self.filename).st_ino
        old_inode = os.fstat(self.fp.fileno()).st_ino
        if inode != old_inode:
            self.fp = file(self.filename)
            self.pos = 0

    def next(self):
        """Return the next line from the file.  Returns None if there are not
        currently any lines available, at which point you should sleep before
        calling again.  Does *not* handle log rotation.  If you use next(), you
        must also use check_inode to handle log rotation"""
        where = self.fp.tell()
        line = self.fp.readline()
        if line and line[-1] == '\n':
            self.pos += len(line)
            return line
        else:
            self.fp.seek(where)
            return None

    def close(self):
        self.fp.close()



class LogTail(Tail):
    def __init__(self, filename):
        self.base_filename = filename
        super(LogTail, self).__init__(filename, -1)

    def get_file(self, inode, next=False):
        files = glob.glob('%s*' % self.base_filename)
        files = [(os.stat(f).st_mtime, f) for f in files]
        # Sort by modification time
        files.sort()

        flag = False
        for mtime, f in files:
            if flag:
                return f
            if os.stat(f).st_ino == inode:
                if next:
                    flag = True
                else:
                    return f
        else:
            return self.base_filename

    def reset(self):
        self.fp = file(self.filename)
        self.pos = 0

    def advance(self):
        self.filename = self.get_file(os.fstat(self.fp.fileno()).st_ino, True)
        self.reset()

    def check_inode(self):
        if self.filename != self.base_filename or os.stat(self.filename).st_ino != os.fstat(self.fp.fileno()).st_ino:
            self.advance()


def main():
    import sys

    t = Tail(sys.argv[1], -1)
    for line in t:
        print line


if __name__ == '__main__':
    main()


