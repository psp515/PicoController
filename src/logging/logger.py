

class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.log_level = 'INFO'
            self.log_file = None

    def log(self, level, message):
        if self._should_log(level):
            log_message = f"[{level}] {message}"
            print(log_message)

    def _should_log(self, level):
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        return levels.index(level) >= levels.index(self.log_level)

    def debug(self, message):
        self.log('DEBUG', message)

    def info(self, message):
        self.log('INFO', message)

    def warning(self, message):
        self.log('WARNING', message)

    def error(self, message):
        self.log('ERROR', message)

    def critical(self, message):
        self.log('CRITICAL', message)
