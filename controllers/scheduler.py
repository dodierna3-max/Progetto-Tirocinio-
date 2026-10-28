import time
import threading
import schedule
from controllers.report_controller import ReportController


class ReportScheduler:

    def __init__(self):
        self.controller = ReportController()

    def _run_loop(self):
        schedule.every().monday.at("08:30").do(self.controller.execute_pipeline, days=7)
        schedule.every().day.at("09:00").do(self.controller.execute_pipeline, days=1)

        while True:
            schedule.run_pending()
            time.sleep(60)

    def start(self):
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()