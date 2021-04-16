import os
import sys

# ref: https://codereview.stackexchange.com/questions/25417/
# to install silently
class NoStdStreams(object):
    def __init__(self,stdout = None, stderr = None, file = ''):
        if not file:
            self.devnull = open(os.devnull,'w')
        else:
            self.devnull = open(file,'w+')
        self._stdout = stdout or self.devnull or sys.stdout
        self._stderr = stderr or self.devnull or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.devnull.close()