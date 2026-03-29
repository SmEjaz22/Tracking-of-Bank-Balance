"""
sms_listener.py

Registers the Java BroadcastReceiver and exposes a Python-side
callback that Kivy's main loop can safely consume.

Usage in main.py:
    from sms_listener import SMSListener
    listener = SMSListener(on_sms_callback=self.handle_sms)
    listener.start()
"""

from kivy.clock import Clock
from kivy.logger import Logger


from kivy.clock import Clock
from kivy.logger import Logger


class SMSListener:

    def __init__(self, on_sms_callback):
        self._callback = on_sms_callback
        self._br = None
        self._running = False

    def start(self):
        if self._running:
            return
        try:
            self._register_receiver()
            self._running = True
            Logger.info("SMSListener: receiver registered")
        except Exception as e:
            Logger.warning(f"SMSListener: could not register ({e})")
            Logger.warning("SMSListener: running in desktop mode — SMS disabled")

    def stop(self):
        if self._br:
            try:
                self._br.stop()
            except Exception:
                pass
        self._running = False

    def _register_receiver(self):
        from android.broadcast import BroadcastReceiver
        self._br = BroadcastReceiver(
            self._on_broadcast,
            actions=['android.provider.Telephony.SMS_RECEIVED']
        )
        self._br.start()

    def _on_broadcast(self, context, intent):
        Logger.info("SMSListener: _on_broadcast called!")
        try:
            from jnius import autoclass
            SmsMessage = autoclass('android.telephony.SmsMessage')
            bundle = intent.getExtras()
            if bundle is None:
                return
            pdus = bundle.get('pdus')
            fmt  = bundle.getString('format')
            if pdus is None:
                return
            for pdu in pdus:
                msg = SmsMessage.createFromPdu(pdu, fmt)
                if msg is None:
                    continue
                sender = msg.getOriginatingAddress()
                body   = msg.getMessageBody()
                Logger.info(f"SMSListener: received from {sender}")
                Clock.schedule_once(
                    lambda dt, s=sender, b=body: self._callback(s, b), 0
                )
        except Exception as e:
            Logger.error(f"SMSListener: error in broadcast handler — {e}")
