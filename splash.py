from kivy.uix.screenmanager import Screen
from kivy.clock import Clock


class SplashScreen(Screen):
    def on_enter(self, *args):
        Clock.schedule_once(self.switch_to_welcome, 5)

    def switch_to_welcome(self, dt):
        self.manager.current = "welcome"
