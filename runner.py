"""Running tests"""

import sys
import time

from . import result
from .signals import registerResult

__unittest = True
SOFT_TAB = ' ' * 2
MAX_LINE_LEN = 60
IN_LINE_SEPERATOR = ' ... '
BASH_COLOR = \
    {
        'green': "\x1b[32;03m",
        'green_bold': "\x1b[32;01m",
        'red': "\x1b[31;03m",
        'red_bold': "\x1b[31;01m",
        'red_under': "\x1b[31;04m",
        'red_blink': "\x1b[31;05m",
        'yellow': "\x1b[33;03m",
        'yellow_bold': "\x1b[33;01m",
        'cyan': "\x1b[36;03m",
        'cyan_bold': "\x1b[36;01m",
        'reset': "\x1b[0m"
    }
def colored_str(text, color):
    """Return colored text."""
    return BASH_COLOR[color] + text + BASH_COLOR['reset']

class _WritelnDecorator(object):
    """Used to decorate file-like objects with a handy 'writeln' method"""
    def __init__(self,stream):
        self.stream = stream

    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream,attr)

    def writeln(self, arg=None):
        if arg:
            self.write(arg)
        self.write('\n') # text-mode streams translate to \r\n if needed


class TextTestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by TextTestRunner.
    """
    separator1 = '=' * 70
    separator2 = '-' * 70
    successes = []

    def __init__(self, stream, descriptions, verbosity):
        super(TextTestResult, self).__init__()
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions

    def writeTestDescription(self, title, flavour, title_color=None, flavour_color=None):
        max_len = MAX_LINE_LEN - len(IN_LINE_SEPERATOR)
        if len(title) > max_len:
            title = title[0:max_len]
        else:
            title += ' ' * (max_len - len(title))
        self.stream.write(SOFT_TAB + colored_str(title, title_color))
        self.stream.write(IN_LINE_SEPERATOR)
        self.stream.writeln(colored_str(flavour, flavour_color))

    def getSummary(self):
        return (colored_str(" PASS:", 'green'), len(self.successes),
                colored_str(" FAIL:", 'red'), len(self.failures),
                colored_str("ERROR:", 'red_bold'), len(self.errors))

    def getDescription(self, test, colored=None):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            case_name = str(test).split(' ')[0]
            if colored:
                return colored_str(case_name, colored)
            else:
                return case_name

    def startTest(self, test):
        super(TextTestResult, self).startTest(test)

    def addSuccess(self, test):
        super(TextTestResult, self).addSuccess(test)
        self.successes.append(test)
        if self.showAll:
            self.writeTestDescription(self.getDescription(test), '[PASS]', 'green', 'green')
        elif self.dots:
            self.stream.write(colored_str('.', 'green'))
            self.stream.flush()

    def addError(self, test, err):
        super(TextTestResult, self).addError(test, err)
        if self.showAll:
            self.writeTestDescription(self.getDescription(test), '[ERROR]', 'red_bold', 'red_bold')
        elif self.dots:
            self.stream.write(colored_str('E', 'red_bold'))
            self.stream.flush()

    def addFailure(self, test, err):
        super(TextTestResult, self).addFailure(test, err)
        if self.showAll:
            self.writeTestDescription(self.getDescription(test), '[FAIL]', 'red', 'red')
        elif self.dots:
            self.stream.write(colored_str('F', 'red'))
            self.stream.flush()

    def addSkip(self, test, reason):
        super(TextTestResult, self).addSkip(test, reason)
        if self.showAll:
            self.stream.writeln("skipped {0!r}".format(reason))
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(TextTestResult, self).addExpectedFailure(test, err)
        if self.showAll:
            self.writeTestDescription(self.getDescription(test), '[EXPECTED]', 'green', 'green')
        elif self.dots:
            self.stream.write(colored_str('x', 'green'))
            self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(TextTestResult, self).addUnexpectedSuccess(test)
        if self.showAll:
            self.writeTestDescription(self.getDescription(test), '[UNEXPECTED]', 'red', 'red')
        elif self.dots:
            self.stream.write(colored_str('u', 'red'))
            self.stream.flush()

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors, color=None):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (colored_str("[" + flavour + "]", 'red_blink'),
                                            self.getDescription(test, 'cyan')))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)


class TextTestRunner(object):
    """A test runner class that displays results in textual form.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    resultclass = TextTestResult

    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, resultclass=None):
        self.stream = _WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        if resultclass is not None:
            self.resultclass = resultclass

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        startTime = time.time()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        run = result.testsRun
        print run
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()
        self.stream.writeln("%s %d\n%s %d\n%s %d" % result.getSummary())
        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        if skipped:
            self.stream.writeln("   SKIPPED:%d" % skipped)
        if expectedFails:
            self.stream.writeln(colored_str("  EXPECTED:%d" % expectedFails, 'green'))
        if unexpectedSuccesses:
            self.stream.writeln(colored_str("UNEXPECTED:%d" % expectedFails, 'red'))
        self.stream.write("\n")
        return result