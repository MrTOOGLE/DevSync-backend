import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class DailyDirectoryFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        self.base_dir = os.path.dirname(filename)
        self.base_filename = os.path.basename(filename)
        self.baseFilename = self.getCurrentFilename()
        super().__init__(self.baseFilename, when=when, interval=interval, backupCount=backupCount,
                         encoding=encoding, delay=delay, utc=utc)

    def getDailyDir(self):
        today = datetime.now().strftime('%Y-%m-%d')
        daily_dir = os.path.join(self.base_dir, today)
        os.makedirs(daily_dir, exist_ok=True)
        return daily_dir

    def getCurrentFilename(self):
        return os.path.join(self.getDailyDir(), self.base_filename)

    def doRollover(self):
        self.baseFilename = self.getCurrentFilename()
        super().doRollover()