import uuid
from secrets import token_hex
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.list import TwoLineRightIconListItem, IconRightWidget
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App


class ContentGroup(MDGridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ContentContact(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class HomeScreen(Screen):
    dialog = None
    t_chatroom = "chatroom"
    t_contact = "contact"
    t_local = "local"
    t_message = "message"
    o = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update(self):
        self.ids.chatroomListWidget.clear_widgets()
        self.ids.contactListWidget.clear_widgets()

        localList = self.o.getDataFromTable(self.t_local, raiseConversionError=True, omitID=False)
        localUUID = localList[1][0][1]

        self.ids.currentUserUUID.text = localUUID
        next_screen = self.parent.get_screen("chat")
        next_screen.user_uuid = localUUID

        chatroomList = self.o.getDataFromTable(self.t_chatroom, raiseConversionError=True, omitID=False)
        chatroomListData = chatroomList[1]

        contactList = self.o.getDataFromTable(self.t_contact, raiseConversionError=True, omitID=False)
        contactListData = contactList[1]

        for g in chatroomListData:
            self.ui_add_chatroom(g[0], g[1], g[2], g[3], g[4])

        for c in contactListData:
            self.ui_add_contact(c[0], c[1], c[2])

    def data_creation_chatroom(self, name, chat_uuid, salt):
        i_chatroom = [name, chat_uuid, salt, True]

        self.o.insertIntoTable(self.t_chatroom, i_chatroom, commit=True)

        contactList = self.o.getDataFromTable(self.t_chatroom, raiseConversionError=True, omitID=False)
        contactListData = contactList[1]
        db_index = contactListData[-1][0]

        self.ui_add_chatroom(db_index, name, chat_uuid, salt, True)

        self.dialog_close()

    def data_creation_contact(self, name, contact_uuid):
        i_contact = [name, contact_uuid]

        self.o.insertIntoTable(self.t_contact, i_contact, commit=True)

        contactList = self.o.getDataFromTable(self.t_contact, raiseConversionError=True, omitID=False)
        contactListData = contactList[1]
        db_index = contactListData[-1][0]

        self.ui_add_contact(db_index, name, contact_uuid)

        self.dialog_close()

    def create_chatroom(self):
        app = App.get_running_app()

        self.dialog = MDDialog(
            title="Add group:",
            type="custom",
            content_cls=ContentGroup(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.dialog_close(),
                ),
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.data_creation_chatroom(self.dialog.content_cls.ids.groupCreationName.text,
                                                                     self.dialog.content_cls.ids.groupCreationUUID.text,
                                                                     self.dialog.content_cls.ids.groupCreationSalt.text) if self.dialog.content_cls.ids.groupcheckbox.active else self.data_creation_chatroom(
                        self.dialog.content_cls.ids.groupCreationName.text, uuid.uuid4().hex, token_hex(32))
                ),
            ],
            radius=[20, 7, 20, 7],
            on_release=lambda x: self.dialog_close(),
        )

        self.dialog.content_cls.ids.groupCreationName.text = ""
        self.dialog.content_cls.ids.groupCreationUUID.text = ""
        self.dialog.content_cls.ids.groupCreationSalt.text = ""
        self.dialog.open()

    def create_contact(self):
        app = App.get_running_app()

        self.dialog = MDDialog(
            title="Create a new contact:",
            type="custom",
            content_cls=ContentContact(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.dialog_close(),
                ),
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=app.theme_cls.primary_color,
                    on_release=lambda x: self.data_creation_contact(
                        self.dialog.content_cls.ids.contactCreationName.text,
                        self.dialog.content_cls.ids.contactCreationUUID.text),
                ),
            ],
            radius=[20, 7, 20, 7],
            on_release=lambda x: self.dialog_close(),
        )

        self.dialog.content_cls.ids.contactCreationName.text = ""
        self.dialog.content_cls.ids.contactCreationUUID.text = ""
        self.dialog.open()

    def remove_chatroom(self, groupID, groupUUID, instance):
        messageList = self.o.getDataFromTable(self.t_message, raiseConversionError=True, omitID=False)
        messageListData = messageList[1]

        for m in messageListData:
            if m[4] == groupUUID:
                self.o.deleteDataInTable(self.t_message, m[0], commit=True, raiseError=True, updateId=False)
        self.o.deleteDataInTable(self.t_chatroom, groupID, commit=True, raiseError=True, updateId=False)

        self.ids.chatroomListWidget.remove_widget(instance)

    def remove_contact(self, contactID, instance):
        self.o.deleteDataInTable(self.t_contact, contactID, commit=True, raiseError=True, updateId=False)
        self.ids.contactListWidget.remove_widget(instance)

    def ui_add_chatroom(self, group_id, name_text, uuid_text, salt, keepMsg):
        nItem = TwoLineRightIconListItem(text=name_text,
                                         secondary_text=uuid_text,)
        nItem.bind(on_release=lambda x: self.go_to_chat(group_id, name_text, uuid_text, salt, keepMsg))
        nIcon = IconRightWidget(icon="trash-can",
                                on_release=lambda x: self.remove_chatroom(group_id, uuid_text, nItem),)
        nItem.add_widget(nIcon)

        self.ids.chatroomListWidget.add_widget(nItem)

    def ui_add_contact(self, contact_id, name_text, uuid_text):
        nItem = TwoLineRightIconListItem(text=name_text,
                                         secondary_text=uuid_text,)
        nIcon = IconRightWidget(icon="trash-can",
                                on_release=lambda x: self.remove_contact(contact_id, nItem),)
        nItem.add_widget(nIcon)

        self.ids.contactListWidget.add_widget(nItem)

    def on_checkbox_active(self, checkbox, value):
        if value:
            self.dialog.content_cls.ids.groupCreationUUID.opacity = 1
            self.dialog.content_cls.ids.groupCreationUUID.disabled = False
            self.dialog.content_cls.ids.groupCreationUUID.required = True

            self.dialog.content_cls.ids.groupCreationSalt.opacity = 1
            self.dialog.content_cls.ids.groupCreationSalt.disabled = False
            self.dialog.content_cls.ids.groupCreationSalt.required = True
        else:
            self.dialog.content_cls.ids.groupCreationUUID.opacity = 0
            self.dialog.content_cls.ids.groupCreationUUID.disabled = True
            self.dialog.content_cls.ids.groupCreationUUID.required = False

            self.dialog.content_cls.ids.groupCreationSalt.opacity = 0
            self.dialog.content_cls.ids.groupCreationSalt.disabled = True
            self.dialog.content_cls.ids.groupCreationSalt.required = False

    def dialog_close(self, *args):
        if self.dialog:
            self.dialog.dismiss(force=True)

    def go_to_chat(self, group_id, name, group_uuid, salt, keepMsg):
        self.parent.current = 'chat'
        next_screen = self.parent.get_screen('chat')
        next_screen.chat_id = group_id
        next_screen.chat_name = name
        next_screen.chat_uuid = group_uuid
        next_screen.chat_salt = salt
        next_screen.keepMsg = keepMsg

    def go_to_contact(self):
        pass
