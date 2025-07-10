import datetime

class Logger:
    def __init__(self, filename='logs/evolution'):
        self.filename = filename + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'
        self.file = open(self.filename, 'w')
        self.start_time = datetime.datetime.now()
    
    def log(self, type='MISC', message='default message'):
        """
        Log a message to the log file with runtime since logger creation
        """
        runtime = datetime.datetime.now() - self.start_time
        self.file.write(f"[{type}] (runtime: {runtime}) {message}\n")
    
    def close(self):
        self.file.close()