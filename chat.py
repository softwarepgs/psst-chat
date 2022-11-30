import json
import time
import base64
import hashlib
import hmac
from secrets import token_hex
import requests
import argon2
import imgurAPI
from threading import Thread
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock, mainthread
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from stegano import lsb
from Cryptodome.Cipher import AES
from Cryptodome import Random
from argon2 import hash_password_raw
from urllib.request import urlopen
from plyer import filechooser

BLOCK_SIZE = 16
pad = lambda s: bytes(s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE), 'utf-8')
unpad = lambda s: s[0:-ord(s[-1:])]
filepath = ""


class Slabel(Label):
    @staticmethod
    def create_sized_label(**kwargs):
        max_width = kwargs.pop('max_width', 0)
        if max_width <= 0:
            return Slabel(**kwargs)

        core_label = CoreLabel(padding=[10, 10], **kwargs)
        core_label.refresh()

        if core_label.width > max_width:
            return Slabel(text_size=(max_width, None), **kwargs)
        else:
            return Slabel(**kwargs)


class ContentP(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ContentInfo(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ChatScreen(Screen):
    chat_layout = ObjectProperty(None)
    filepath = None
    dialog = None
    task = None
    chat_id = None
    chat_name = None
    chat_uuid = None
    chat_salt = None
    keepMsg = None
    user_uuid = None
    pwd = None
    o = None
    working = None
    t_message = "message"

    def update(self):
        print(self.chat_name)
        print(self.chat_uuid)
        print(self.chat_salt)
        print(self.keepMsg)
        print(self.user_uuid)

        self.ids.gallerybutton.disabled = True
        self.ids.chatbox.disabled = True
        self.ids.sendbutton.disabled = True

        self.ids.chat_layout.clear_widgets()

        self.update_store_widget()

        messageList = self.o.getDataFromTable(self.t_message, raiseConversionError=True, omitID=False)
        messageListData = messageList[1]

        for m in messageListData:
            if m[4] == self.chat_uuid:
                self.m_builder(m[1], m[2], m[3])

        if self.pwd is None:
            self.pwd_insert()

        self.task = Clock.schedule_interval(self.start_get_messages_thread, 60)

    def pwd_insert(self):
        app = App.get_running_app()

        self.dialog = MDDialog(
            title="Insert passphrase:",
            type="custom",
            content_cls=ContentP(),
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.setup_pwd(),
                ),
            ],
            radius=[20, 7, 20, 7],
        )

        self.dialog.content_cls.ids.chatPassphrase.text = ""
        self.dialog.open()

    def setup_pwd(self):
        self.ids.gallerybutton.disabled = False
        self.ids.chatbox.disabled = False
        self.ids.sendbutton.disabled = False
        self.pwd = self.dialog.content_cls.ids.chatPassphrase.text
        self.dialog_close()

    def access_internet(self):
        try:
            response = urlopen('http://amionline.net/', timeout=10)
            return True
        except:
            return False

    def safe_internet(self):
        x = self.access_internet()
        if not x:
            self.ids.gallerybutton.disabled = True
            self.ids.chatbox.disabled = True
            self.ids.sendbutton.disabled = True
            Clock.schedule_once(self.popup_error("No internet connection. Functionality will be limited."
                                                 "Please re-enter group after connecting to internet."))
            return False
        else:
            return True

    @mainthread
    def popup_error(self, msg):
        self.dialog = MDDialog(
            title="Error",
            size_hint=(.6, None),
            text=msg,
            on_release=lambda x: self.dialog_close(),
        )
        self.dialog.open()

    def start_get_messages_thread(self, arg):
        if self.working is None:
            self.working = True
            Thread(target=self.get_messages).start()

    def start_send_message_thread(self):
        if self.working is None:
            self.working = True
            Thread(target=self.send_message).start()

    def get_messages(self):
        if self.pwd is None:
            return

        self.ids.backbutton.disabled = True
        self.ids.dotsbutton.disabled = True
        self.ids.gallerybutton.disabled = True
        self.ids.chatbox.disabled = True
        self.ids.sendbutton.disabled = True

        net = self.safe_internet()
        if not net:
            return

        ci = self.get_key(self.pwd, self.chat_salt)
        plaintext = self.download_function(self.chat_uuid, ci)

        if plaintext is None:
            self.ids.backbutton.disabled = False
            self.ids.dotsbutton.disabled = False
            self.ids.gallerybutton.disabled = False
            self.ids.chatbox.disabled = False
            self.ids.sendbutton.disabled = False
            return

        for p in plaintext:
            text = p.split("&#")

            sender = text[0]
            content = text[1]
            timestamp = text[2]

            self.m_builder(sender, content, timestamp)

            if self.keepMsg == "False":
                pass
            else:
                i_message = [sender, content, timestamp, self.chat_uuid]
                self.o.insertIntoTable(self.t_message, i_message, commit=True)

        self.ids.backbutton.disabled = False
        self.ids.dotsbutton.disabled = False
        self.ids.gallerybutton.disabled = False
        self.ids.chatbox.disabled = False
        self.ids.sendbutton.disabled = False
        self.working = None

    def send_message(self):
        if self.filepath is None:
            self.popup_error("Please choose an image to hide data.")
        else:
            if self.ids.chatbox.text == "":
                self.popup_error("Please write a message.")
            else:
                net = self.safe_internet()
                if not net:
                    return

                self.ids.backbutton.disabled = True
                self.ids.dotsbutton.disabled = True
                self.ids.gallerybutton.disabled = True
                self.ids.chatbox.disabled = True
                self.ids.sendbutton.disabled = True

                path = self.filepath.replace("\\", "/")
                filename = path.split("/")
                f = filename[-1]
                f = token_hex(8) + f[-4:]

                msg = self.user_uuid
                msg += "&#"
                msg += self.ids.chatbox.text
                msg += "&#"
                t = time.time()
                msg += str(t)

                ci = self.get_key(self.pwd, self.chat_salt)
                result = self.upload_function(path, f, msg, self.chat_uuid, ci)

                if result:
                    if self.keepMsg == "False":
                        pass
                    else:
                        i_message = [self.user_uuid, self.ids.chatbox.text, t, self.chat_uuid]
                        self.o.insertIntoTable(self.t_message, i_message, commit=True)
                    self.m_builder(self.user_uuid, self.ids.chatbox.text, t)
                    self.ids.backbutton.disabled = False
                    self.ids.dotsbutton.disabled = False
                    self.ids.gallerybutton.disabled = False
                    self.ids.chatbox.disabled = False
                    self.ids.sendbutton.disabled = False
                    self.working = None
                else:
                    self.ids.backbutton.disabled = False
                    self.ids.dotsbutton.disabled = False
                    self.ids.gallerybutton.disabled = False
                    self.ids.chatbox.disabled = False
                    self.ids.sendbutton.disabled = False
                    self.working = None

    @mainthread
    def m_builder(self, s, c, t):
        max_width = (self.chat_layout.width - self.chat_layout.spacing - self.chat_layout.padding[0] -
                     self.chat_layout.padding[2]) * 0.75

        if s == self.user_uuid:
            self.chat_layout.add_widget(
                Slabel.create_sized_label(text=c, max_width=max_width,
                                          font_name='Roboto',
                                          font_size=15, pos_hint={'right': 1}))
        else:
            self.chat_layout.add_widget(
                Slabel.create_sized_label(text=c, max_width=max_width,
                                          font_name='Roboto',
                                          font_size=15, pos_hint={'x': 0}))

        self.ids.scroll.scroll_y = 0
        self.ids.chatbox.text = ""

    def file_manager(self):
        try:
            self.filepath = filechooser.open_file()[0]
        except:
            return

        if self.filepath[-4:] != ".png" and self.filepath[-4:] != ".PNG" and self.filepath[-4:] != ".jpg" and \
                self.filepath[-4:] != ".JPG" and self.filepath[-5:] != ".jpeg" and self.filepath[-5:] != ".JPEG":
            self.popup_error("File format not accepted. Please use png or jpg.")

    def get_key(self, pwd, s):
        k = hash_password_raw(
            time_cost=16, memory_cost=2 ** 15, parallelism=2, hash_len=32, password=pwd.encode("utf-8"),
            salt=s.encode("utf-8"), type=argon2.low_level.Type.ID
        )  # key derivation function initialization & key created (nonce/salt used as well)
        return k

    def check_signature(self, sig1, sig2):
        return sig1 == sig2

    def encrypt(self, raw, key):
        iv = Random.new().read(AES.block_size)  # iv generation
        cipher = AES.new(key, AES.MODE_CBC, iv)  # cipher object
        paddedRaw = pad(raw)  # plaintext padding
        ei = cipher.encrypt(paddedRaw)  # plaintext encryption
        hi = hmac.new(iv, ei, hashlib.sha256).hexdigest()  # hmac generation
        eiHex = ei.hex()  # cyphertext bynary to hex
        tMsg = hi + eiHex  # prepend hmac to cyphertext
        padMsg = pad(tMsg)  # pad hmac+cyphertext
        cipher = AES.new(key, AES.MODE_CBC, iv)  # cipher object refresh
        etMsg = cipher.encrypt(padMsg)  # encrypt hmac+cyphertext
        return base64.b64encode(iv + etMsg)

    def decrypt(self, enc, key):
        enc = base64.b64decode(enc)
        iv = enc[:16]  # grab IV, located in first 16 bytes
        cipher = AES.new(key, AES.MODE_CBC, iv)  # cipher object
        etMsg = enc[16:]  # grab hmac+cyphertext

        try:
            padMsg = cipher.decrypt(etMsg)  # decrypt hmac+cyphertext
        except:
            self.popup_error("Error occured during decryption - key was not accepted.")
            return

        tMsg = unpad(padMsg)  # unpad hmac+cyphertext
        hi = tMsg[:64].decode("utf-8")  # grab hmac, first 64 bytes
        eiHex = tMsg[64:len(tMsg)]  # grab cyphertext, remaining bytes
        ei = bytes.fromhex(eiHex.decode("ascii"))  # turn cyphertext to binary from hex
        ahi = hmac.new(iv, ei, hashlib.sha256).hexdigest()  # generate new hmac from iv and cyphertext

        if not self.check_signature(hi, ahi):
            self.popup_error("Signature mismatch - file has been compromised.")
        else:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            paddedRaw = cipher.decrypt(ei)
            unpaddedRaw = unpad(paddedRaw)
            return unpaddedRaw

    def upload_function(self, imgOriginal, imgSecret, msg, room, ci):
        geturl = 'https://api.dontpad.com/' + room + '.body.json'
        posturl = 'https://api.dontpad.com/' + room

        finalMsg = ""

        mi = self.encrypt(msg, ci)

        try:
            sfi = lsb.hide(imgOriginal, mi.hex())  # message hidden in image
        except:
            self.popup_error("Image not appropriate for steganography.")
            return

        sfi.save(imgSecret)  # altered image file saved

        imageName = "testImage"
        imageTitle = "Test"

        try:
            with open(imgSecret, "rb") as secretImage:
                data = base64.b64encode(secretImage.read())
                result = imgurAPI.uploadImageAnonymous(data, imageName, imageTitle)
        except:
            return

        payload = {'lastModified': '0'}
        response = requests.get(geturl, data=payload)

        responseJSON = json.loads(response.text)
        text = responseJSON['body']

        if text is None:
            pass
        else:
            finalMsg += text + "\n"

        finalMsg += self.user_uuid
        finalMsg += "##"
        finalMsg += result
        print(finalMsg)

        payload = {'text': finalMsg}
        requests.post(posturl, data=payload)

        return True

    def download_function(self, room, ci):
        geturl = 'https://api.dontpad.com/' + room + '.body.json'
        posturl = 'https://api.dontpad.com/' + room
        rewrite = ""

        plaintextList = []

        payload = {'lastModified': '0'}
        response = requests.get(geturl, data=payload)

        responseJSON = json.loads(response.text)
        text = responseJSON['body']

        if text is None:
            return

        lines = text.split("\n")

        for content in lines:
            if content == "":
                break
            altered_content = content.split("##")
            sender = altered_content[0]
            imageUrl = altered_content[1]

            if sender != self.user_uuid:
                try:
                    image = requests.get(imageUrl).content
                except:
                    self.popup_error("Could not retrieve image from Imgur.")
                    return

                x = imageUrl.split("/")
                filename = x[3]

                path = "files/"
                path += filename

                with open(path, "wb") as handler:
                    handler.write(image)

                try:
                    mi = lsb.reveal(path)  # secret message is revealed
                except:
                    self.popup_error("Could not retrieve hidden data from image. Steganography compromised.")
                    return

                plaintext = self.decrypt(bytes.fromhex(mi), ci)
                plaintextList.append(plaintext.decode("utf-8"))
            else:
                rewrite += content + "\n"

        if rewrite == "":
            payload = {'text': ''}
            requests.post(posturl, data=payload)
        else:
            payload = {'text': rewrite}
            requests.post(posturl, data=payload)

        return plaintextList

    def room_info(self):
        app = App.get_running_app()

        self.dialog = MDDialog(
            title="Chatroom Information",
            type="custom",
            content_cls=ContentInfo(),
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.dialog_close(),
                ),
            ],
            radius=[20, 7, 20, 7],
        )

        self.dialog.content_cls.ids.roomname.text = "Name:" + self.chat_name
        self.dialog.content_cls.ids.roomuuid.text = "Chat UUID: " + self.chat_uuid
        self.dialog.content_cls.ids.roomsalt.text = "Salt: " + self.chat_salt

        self.dialog.open()

    def update_store_widget(self):
        if self.keepMsg == "True":
            self.ids.dbswitch.active = True
        else:
            self.ids.dbswitch.active = False

    def on_switch_active(self, checkbox, value):
        if value:
            self.keepMsg = True
            self.o.updateInTable("chatroom", self.chat_id, "keepMsg", True, commit=True, raiseError=True)
        else:
            self.keepMsg = False
            self.o.updateInTable("chatroom", self.chat_id, "keepMsg", False, commit=True, raiseError=True)

    def go_back(self):
        self.task.cancel()
        self.ids.chat_layout.clear_widgets()

        self.chat_id = None
        self.chat_name = None
        self.chat_uuid = None
        self.chat_salt = None
        self.keepMsg = None
        self.pwd = None
        self.parent.current = "home"

    def dialog_close(self, *args):
        if self.dialog:
            self.dialog.dismiss(force=True)
