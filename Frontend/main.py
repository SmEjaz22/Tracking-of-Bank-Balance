import kivy
from kivy.core import text
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.lang import Builder

# kivy.require("2.3.1")

Builder.load_file("firstappofmine.kv")  # Adds the .kv file path here,
# class MygridLayout(Widget):


class Login(GridLayout):
    # Comment the __init__ after the creation of .kv file.
    def __init__(self, **kwargs):
        super(Login, self).__init__(**kwargs)

        self.cols = 1
        self.add_widget(Label(text="User Name"))
        self.username = TextInput()
        self.add_widget(self.username)

        self.add_widget(Label(text="Password"))
        self.password = TextInput(password=True)
        self.add_widget(self.password)

        # Create a submit button
        self.submit = Button(text="Login")

        # Make button bind
        self.submit.bind(
            on_press=self.ProcessLogin
        )  # When binding things we are passing an instance

        self.add_widget(self.submit)

        self.error = Label(text="")
        self.add_widget(self.error)

    def ProcessLogin(self, instance):
        self.error.text = ""  # clear previous messages

        if not self.username.text or not self.password.text:
            self.error.text = "Please fill the login form"
            return False
        self.error.text = f"Logging {self.username.text} in..."
        return True


class FirstAppOfMine(App):
    def build(self):
        return Login()


if __name__ == "__main__":
    FirstAppOfMine().run()


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
