import gc


class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, level: str = 'INFO'):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._level = level

    def log(self, level, message):
        if self._should_log(level):
            log_message = f"[{level}] {message}"
            print(log_message)

    def _should_log(self, level) -> bool:
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        return levels.index(level) >= levels.index(self._level)

    def is_debug(self) -> bool:
        return self._should_log('DEBUG')

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
        free_memory = gc.mem_free()
        allocated_memory = gc.mem_alloc()
        self.log('CRITICAL', f"Free memory: {free_memory} bytes, Allocated memory: {allocated_memory} bytes.")
