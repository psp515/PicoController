from logger.base import Appender


class ConsoleAppender(Appender):
    def append(self, line):
        print(line)
