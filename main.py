import asyncio

from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

from splash import SplashScreen
from welcome import WelcomeScreen
from home import HomeScreen
from chat import ChatScreen

Builder.load_file('screens/screen_management.kv')
Builder.load_file('screens/splash.kv')
Builder.load_file('screens/welcome.kv')
Builder.load_file('screens/home.kv')
Builder.load_file('screens/chat.kv')

Window.size = (350, 600)


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.title = "PSST"

        sm = ScreenManager(transition=SlideTransition())
        screens = [
            SplashScreen(name="splash"),
            WelcomeScreen(name="welcome"),
            HomeScreen(name="home"),
            ChatScreen(name="chat")
        ]
        for screen in screens:
            sm.add_widget(screen)

        return sm


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        MainApp().async_run()
    )
    loop.close()
