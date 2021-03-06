from data.watch_session import WatchSession
from threading import Thread
import traceback
import time
from pts.scrobbler import Scrobbler


class SessionManager(Thread):
    def __init__(self):
        self.active = True

        super(SessionManager, self).__init__()

    def run(self):
        while self.active:
            try:
                self.check_sessions()
            except Exception, ex:
                trace = traceback.format_exc()
                Log.Warn('Exception from SessionManager (%s): %s' % (ex, trace))

            time.sleep(2)

    def check_sessions(self):
        sessions = WatchSession.all()

        if not len(sessions):
            return

        for key, session in sessions:
            self.check_paused(session)

    def check_paused(self, session):
        if session.cur_state != 'paused' or not session.paused_since:
            return

        if session.watching and Datetime.Now() > session.paused_since + Datetime.Delta(seconds=15):
            Log.Debug("%s paused for 15s, watching status cancelled" % session.get_title())
            session.watching = False
            session.save()

            if not self.send_action(session, 'cancelwatching'):
                Log.Info('Failed to cancel the watching status')

    def send_action(self, session, action):
        media_type = session.get_type()
        if not media_type:
            return False

        if Scrobbler.handle_action(session, media_type, action, session.cur_state):
            return False

        Dict.Save()
        return True

    def stop(self):
        self.active = False
