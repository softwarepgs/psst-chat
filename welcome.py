from kivy.properties import BooleanProperty
from kivymd.uix.dialog import MDDialog
from kivy.uix.screenmanager import Screen
from pathlib import Path
from pysqlitecipher import sqlitewrapper
from pysqlitecipher.sqlitewrapper import SqliteCipher
from db import db_setup
from kivy.app import App


class WelcomeScreen(Screen):
    dialog = None
    password_mode = BooleanProperty(True)

    path_to_file = "db/pydatabase.db"
    path = Path(path_to_file)
    f = None

    def check_file(self):
        if not self.path.is_file():
            self.f = False
            self.ids.wsPasswordConfirm.required = True
            self.ids.wsPasswordConfirm.opacity = 1
            self.ids.wsPasswordConfirm.disabled = False
        else:
            self.f = True
            pass

    def startup_message(self, message):
        self.dialog = MDDialog(
            text=message,
            radius=[20, 7, 20, 7],
            on_release=self.dialog_close,
        )
        self.dialog.open()

    def dialog_close(self, *args):
        if self.dialog:
            self.dialog.dismiss(force=True)

    def press_ok(self):
        if self.f:
            x = SqliteCipher.getVerifier(dataBasePath="db/pydatabase.db", checkSameThread=False)
            y = SqliteCipher.sha512Convertor(self.ids.wsPassword.text)
            if x == y:
                self.parent.current = "home"
                obj = sqlitewrapper.SqliteCipher(dataBasePath="db/pydatabase.db", checkSameThread=False,
                                                 password=self.ids.wsPassword.text)
                App.get_running_app().root.get_screen('home').o = obj
                App.get_running_app().root.get_screen('chat').o = obj
                self.startup_message("Welcome back.")
            else:
                self.startup_message("Password incorrect.")
        else:
            if self.ids.wsPassword.text == self.ids.wsPasswordConfirm.text:
                db_setup.db_creation(self.ids.wsPassword.text)
                obj = sqlitewrapper.SqliteCipher(dataBasePath="db/pydatabase.db", checkSameThread=False,
                                                 password=self.ids.wsPassword.text)
                App.get_running_app().root.get_screen('home').o = obj
                App.get_running_app().root.get_screen('chat').o = obj
                self.parent.current = "home"
                self.startup_message("Please do not forget your password. You will need it whenever you open this app.")
            else:
                self.startup_message("Passwords do not match. Try again.")
