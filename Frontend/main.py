import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.logger import Logger
import threading
import requests

from sms_listener import SMSListener
from sms_parser import parse


# ---------------------------------------------------------------------------
# Config — point this at your Django server
# On a real device, 127.0.0.1 won't work — use your machine's local IP
# e.g. http://192.168.1.10:8000
# ---------------------------------------------------------------------------
API_BASE = "http://192.168.100.248/24:8000/api" # Change it to my machine's IP
TOKEN    = ""   # filled after login


# ---------------------------------------------------------------------------
# API helpers (run in background threads — never block the UI)
# ---------------------------------------------------------------------------

def api_login(username, password, on_success, on_error):
    def run():
        try:
            r = requests.post(f"{API_BASE}/auth/login/", json={
                "username": username,
                "password": password,
            }, timeout=10)
            if r.status_code == 200:
                Clock.schedule_once(lambda dt: on_success(r.json()), 0)
            else:
                Clock.schedule_once(lambda dt: on_error(r.json()), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: on_error({"error": str(e)}), 0)
    threading.Thread(target=run, daemon=True).start()


def api_suggest(amount, direction, source_bank, on_result):
    def run():
        try:
            r = requests.post(f"{API_BASE}/suggest/", json={
                "amount":      amount,
                "direction":   direction,
                "source_bank": source_bank,
            }, headers={"Authorization": f"Token {TOKEN}"}, timeout=10)
            Clock.schedule_once(lambda dt: on_result(r.json()), 0)
        except Exception as e:
            Logger.error(f"API: suggest failed — {e}")
    threading.Thread(target=run, daemon=True).start()


def api_log_transaction(pocket_id, amount, direction,
                        source_bank, raw_sms, assigned_by,
                        confidence_score, on_done):
    def run():
        from datetime import datetime, timezone
        try:
            r = requests.post(f"{API_BASE}/transactions/", json={
                "pocket":          str(pocket_id),
                "amount":          amount,
                "direction":       direction,
                "source_bank":     source_bank,
                "raw_sms":         raw_sms,
                "assigned_by":     assigned_by,
                "confidence_score": confidence_score,
                "transacted_at":   datetime.now(timezone.utc).isoformat(),
            }, headers={"Authorization": f"Token {TOKEN}"}, timeout=10)
            if on_done:
                Clock.schedule_once(lambda dt: on_done(r.json()), 0)
        except Exception as e:
            Logger.error(f"API: log transaction failed — {e}")
    threading.Thread(target=run, daemon=True).start()


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

class GridLayoutExample(GridLayout):

    mytotal      = StringProperty("My Total:")
    mytotalvalue = StringProperty("____")
    mysalary     = StringProperty("")
    mysaving     = StringProperty("")
    myothers     = StringProperty("")

    # Holds the last parsed SMS while we wait for the suggestion response
    _pending_sms = None

    def on_kv_post(self, base_widget):
        """Called after the kv file is loaded — safe place to start services."""
        # self._start_sms_listener()
        self._request_sms_permission()

    def _request_sms_permission(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions(
                [Permission.RECEIVE_SMS, Permission.READ_SMS],
                self._on_permissions_result
            )
        except ImportError:
            # Desktop — skip
            self._start_sms_listener()

    def _on_permissions_result(self, permissions, grant_results):
        if all(grant_results):
            Logger.info("Permissions: SMS granted")
            self._start_sms_listener()
        else:
            Logger.warning("Permissions: SMS denied")



    def _start_sms_listener(self):
        self.listener = SMSListener(on_sms_callback=self._on_sms_received)
        self.listener.start()

    # ------------------------------------------------------------------
    # SMS received — runs on the Kivy main thread (Clock scheduled)
    # ------------------------------------------------------------------
    def _on_sms_received(self, sender: str, body: str):
        result = parse(sender, body)
        if result is None:
            return  # not a bank transaction, ignore

        Logger.info(f"SMS: {result.bank} {result.direction} Rs {result.amount:,}")

        # Store while we wait for the API
        self._pending_sms = {
            "parsed":  result,
            "raw_sms": body,
        }

        # Ask Django for a pocket suggestion
        api_suggest(
            amount      = result.amount,
            direction   = result.direction,
            source_bank = result.bank,
            on_result   = self._on_suggestion_received,
        )

    # ------------------------------------------------------------------
    # Suggestion response from Django
    # ------------------------------------------------------------------
    def _on_suggestion_received(self, data: dict):
        if self._pending_sms is None:
            return

        parsed   = self._pending_sms["parsed"]
        raw_sms  = self._pending_sms["raw_sms"]
        action   = data.get("action", "none")
        pocket_id    = data.get("suggested_pocket_id")
        pocket_name  = data.get("suggested_pocket_name", "")
        confidence   = data.get("confidence", 0.0)

        Logger.info(f"Suggestion: action={action} pocket={pocket_name} conf={confidence:.0%}")

        if action == "auto" and pocket_id:
            # High confidence — assign silently and notify
            self._auto_assign(parsed, raw_sms, pocket_id, pocket_name, confidence)

        elif action == "suggestion" and pocket_id:
            # Medium confidence — show UI with pre-selection
            self._show_pocket_sheet(parsed, raw_sms,
                                    preselect_id=pocket_id,
                                    preselect_name=pocket_name,
                                    confidence=confidence)
        else:
            # No data yet — show all pockets, let user pick
            self._show_pocket_sheet(parsed, raw_sms,
                                    preselect_id=None,
                                    preselect_name=None,
                                    confidence=0.0)

        self._pending_sms = None

    # ------------------------------------------------------------------
    # Auto-assign (confidence >= 0.85)
    # ------------------------------------------------------------------
    def _auto_assign(self, parsed, raw_sms, pocket_id, pocket_name, confidence):
        api_log_transaction(
            pocket_id       = pocket_id,
            amount          = parsed.amount,
            direction       = parsed.direction,
            source_bank     = parsed.bank,
            raw_sms         = raw_sms,
            assigned_by     = "auto",
            confidence_score= confidence,
            on_done         = None,
        )
        # TODO: fire local Android notification here
        # For now, log it so you can see it working
        Logger.info(
            f"Auto-assigned: Rs {parsed.amount:,} {parsed.direction} → {pocket_name}"
        )

    # ------------------------------------------------------------------
    # Show pocket picker bottom sheet (confidence < 0.85)
    # ------------------------------------------------------------------
    def _show_pocket_sheet(self, parsed, raw_sms,
                           preselect_id, preselect_name, confidence):
        # TODO: open Kivy bottom sheet UI
        # For now, log so you can confirm the flow reaches here
        Logger.info(
            f"Show sheet: Rs {parsed.amount:,} {parsed.direction} "
            f"from {parsed.bank} — preselect: {preselect_name}"
        )

    # ------------------------------------------------------------------
    # Existing toggle methods (your original code)
    # ------------------------------------------------------------------
    def showtotal(self):
        if "____" in self.mytotalvalue:
            self.mytotalvalue = "2000"
        else:
            self.mytotalvalue = "____"

    def showsalary(self):
        self.mysalary = "900$" if not self.mysalary else ""

    def showsaving(self):
        self.mysaving = "900$" if not self.mysaving else ""

    def showothers(self):
        self.myothers = "900$" if not self.myothers else ""


class FirstAppOfMine(App):
    def build(self):
        return GridLayoutExample()


if __name__ == "__main__":
    FirstAppOfMine().run()










# import kivy
# from kivy.core import text
# from kivy.app import App
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.label import Label
# from kivy.uix.textinput import TextInput
# from kivy.uix.gridlayout import GridLayout
# from kivy.uix.button import Button
# from kivy.uix.widget import Widget
# from kivy.lang import Builder
# from kivy.properties import StringProperty, BooleanProperty
#
# # kivy.require("2.3.1")
#
# # Practicing
#
#
# class BoxLayoutExample(BoxLayout):
#     pass
#
#
# class GridLayoutExample(GridLayout):
#     # gridlayout doesnot allow the pos_hint values in kv file. But uses the cols/rows feature. Otherwise the things will override eachother.
#     pass
#
#     mytotal = StringProperty("My Total:")
#     mytotalvalue = StringProperty("____")
#     mysalary = StringProperty("My Sal: ")
#     mysalaryvalue = StringProperty("____")
#     mysaving = StringProperty("My Sav: ")
#     mysavingvalue = StringProperty("____")
#     myothers = StringProperty("My Oth: ")
#     myothersvalue = StringProperty("____")
#
#     def showtotal(self):
#         if "____" in self.mytotalvalue:
#             self.mytotalvalue = "2000"
#         else:
#             self.mytotalvalue = "____"
#
#     def showsalary(self):
#         if "____" in self.mysalaryvalue:
#             self.mysalaryvalue = "900$"
#         else:
#             self.mysalaryvalue = "____"
#
#     def showsaving(self):
#         if "____" in self.mysavingvalue:
#             self.mysavingvalue = "900$"
#         else:
#             self.mysavingvalue = "____"
#
#     def showothers(self):
#         if "____" in self.myothersvalue:
#             self.myothersvalue = "900$"
#         else:
#             self.myothersvalue = "____"
#
#     # def togglebutton(self, tb):
#     #     if tb.state == "normal":
#     #         tb.text = "OFF"
#     #     else:  # tb.state == 'down'
#     #         tb.text = "ON"
#
#     # def activeswitch(self, sw):
#     #     print(sw.active)
#
#     slider_value_txt = StringProperty()
#
#     def changeslider(self, sl):
#         print("Slider is at: " + str(int(sl.value)))
#         self.slider_value_txt = str(int(sl.value))
#
#
# class FirstAppOfMine(App):
#     def build(self):
#         return GridLayoutExample()
#         # return BoxLayoutExample()
#
#         # Class rule only (<ClassName>) + Python returns instance
#         # Root rule only (ClassName:) + Python returns nothing
#
#
# if __name__ == "__main__":
#     FirstAppOfMine().run()
#

# Builder.load_file("firstappofmine.kv")  # Adds the .kv file path here,
# # class MygridLayout(Widget):
#
#
# class Login(GridLayout):
#     # Comment the __init__ after the creation of .kv file.
#     def __init__(self, **kwargs):
#         super(Login, self).__init__(**kwargs)
#
#         self.cols = 1
#         self.add_widget(Label(text="User Name"))
#         self.username = TextInput()
#         self.add_widget(self.username)
#
#         self.add_widget(Label(text="Password"))
#         self.password = TextInput(password=True)
#         self.add_widget(self.password)
#
#         # Create a submit button
#         self.submit = Button(text="Login")
#
#         # Make button bind
#         self.submit.bind(
#             on_press=self.ProcessLogin
#         )  # When binding things we are passing an instance
#
#         self.add_widget(self.submit)
#
#         self.error = Label(text="")
#         self.add_widget(self.error)
#
#     def ProcessLogin(self, instance):
#         self.error.text = ""  # clear previous messages
#
#         if not self.username.text or not self.password.text:
#             self.error.text = "Please fill the login form"
#             return False
#         self.error.text = f"Logging {self.username.text} in..."
#         return True
#
#
# class FirstAppOfMine(App):
#     def build(self):
#         return Login()
#
#
# if __name__ == "__main__":
#     FirstAppOfMine().run()
#

# """
# Pocket App - Personal Finance Manager
# Modular and scalable architecture
# """
#
# from kivy.app import App
# from kivy.uix.screenmanager import ScreenManager, FadeTransition
# from kivy.core.window import Window
# from kivy.utils import get_color_from_hex
# from kivy.clock import Clock
# from kivy.logger import Logger
# from kivy.properties import ObjectProperty, DictProperty
#
# from core.config import Config
# from services.api_client import APIClient
# from services.auth_service import AuthService
# from services.sms_listener import SMSListener
# from utils.storage import SecureStorage
#
# # Import screens
# from screens.login_screen import LoginScreen
# from screens.dashboard_screen import DashboardScreen
# from screens.pocket_detail_screen import PocketDetailScreen
# from screens.transaction_screen import TransactionScreen
#
#
# class PocketApp(App):
#     """Main application class"""
#
#     # Properties accessible throughout app
#     api_client = ObjectProperty(None)
#     auth_service = ObjectProperty(None)
#     storage = ObjectProperty(None)
#     current_user = DictProperty({})
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.config = Config
#         self.logger = Logger
#         self.screens = {}
#
#     def build(self):
#         """Build the application"""
#         # Window setup
#         Window.clearcolor = get_color_from_hex("#F5F5F5")
#         Window.minimum_width = 350
#         Window.minimum_height = 600
#
#         # Initialize services
#         self._init_services()
#
#         # Create screen manager
#         self.sm = ScreenManager(transition=FadeTransition())
#
#         # Add screens
#         self._add_screens()
#
#         # Check if user is already logged in
#         self._check_initial_route()
#
#         return self.sm
#
#     def _init_services(self):
#         """Initialize all services"""
#         self.logger.info("Initializing services...")
#
#         # Secure storage
#         self.storage = SecureStorage()
#
#         # API client
#         self.api_client = APIClient(
#             base_url=self.config.API_BASE_URL,
#             timeout=self.config.API_TIMEOUT,
#             storage=self.storage,
#         )
#
#         # Auth service
#         self.auth_service = AuthService(
#             api_client=self.api_client, storage=self.storage
#         )
#
#         # SMS listener (starts after login)
#         self.sms_listener = SMSListener(self)
#
#         self.logger.info("Services initialized")
#
#     def _add_screens(self):
#         """Add all screens to manager"""
#         screens = {
#             "login": LoginScreen,
#             "dashboard": DashboardScreen,
#             "pocket_detail": PocketDetailScreen,
#             "transaction": TransactionScreen,
#         }
#
#         for name, screen_class in screens.items():
#             screen = screen_class(name=name)
#             screen.app = self
#             self.sm.add_widget(screen)
#             self.screens[name] = screen
#
#     def _check_initial_route(self):
#         """Check if user is logged in"""
#         if self.auth_service.is_authenticated():
#             self.logger.info("User already authenticated")
#             self.current_user = self.auth_service.get_current_user()
#             self.sm.current = "dashboard"
#             self.start_sms_listener()
#         else:
#             self.sm.current = "login"
#
#     def start_sms_listener(self):
#         """Start listening for SMS"""
#         if self.sms_listener:
#             self.sms_listener.start()
#
#     def stop_sms_listener(self):
#         """Stop listening for SMS"""
#         if self.sms_listener:
#             self.sms_listener.stop()
#
#     def show_snackbar(self, message: str, error: bool = False, success: bool = False):
#         """Show snackbar message"""
#         # Will implement with KivyMD's Snackbar
#         from kivymd.uix.snackbar import Snackbar
#
#         bg_color = (
#             self.config.DANGER_COLOR
#             if error
#             else self.config.SUCCESS_COLOR
#             if success
#             else self.config.PRIMARY_COLOR
#         )
#
#         Snackbar(text=message, bg_color=bg_color, duration=3).open()
#
#     def show_loading(self, show: bool = True):
#         """Show/hide loading indicator"""
#         # Will implement with MDDialog or custom overlay
#         pass
#
#     def on_pause(self):
#         """Handle app pause (Android)"""
#         self.stop_sms_listener()
#         return True
#
#     def on_resume(self):
#         """Handle app resume (Android)"""
#         if self.auth_service.is_authenticated():
#             self.start_sms_listener()
#
#     def logout(self):
#         """Logout user"""
#         self.auth_service.logout()
#         self.current_user = {}
#         self.stop_sms_listener()
#         self.sm.current = "login"
#
#
# if __name__ == "__main__":
#     PocketApp().run()
