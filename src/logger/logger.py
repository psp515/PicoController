import time

LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40}


class Logger:
    def __init__(self, state, appenders=None):
        self._state = state
        self._appenders = appenders or []

    def add_appender(self, appender):
        self._appenders.append(appender)

    def _enabled(self):
        return self._state.get("logging", "enabled", default=False)

    def _threshold(self):
        name = self._state.get("logging", "level", default="info")
        return LEVELS.get(name, LEVELS["info"])

    def log(self, level, element, message, *args, **kwargs):
        if not self._enabled():
            return
        if LEVELS.get(level, LEVELS["info"]) < self._threshold():
            return
        if args or kwargs:
            message = message.format(*args, **kwargs)
        line = "[{}] {} {}: {}".format(time.ticks_ms(), level, element, message)
        for appender in self._appenders:
            appender.append(line)

    def debug(self, element, message, *args, **kwargs):
        self.log("debug", element, message, *args, **kwargs)

    def info(self, element, message, *args, **kwargs):
        self.log("info", element, message, *args, **kwargs)

    def warning(self, element, message, *args, **kwargs):
        self.log("warning", element, message, *args, **kwargs)

    def error(self, element, message, *args, **kwargs):
        self.log("error", element, message, *args, **kwargs)
