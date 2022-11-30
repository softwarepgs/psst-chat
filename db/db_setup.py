import uuid
from pysqlitecipher import sqlitewrapper


def db_creation(fp):
    t_chatroom = "chatroom"
    t_contact = "contact"
    t_message = "message"
    t_local = "local"

    c_chatroom = [
        ["name", "TEXT"],
        ["uuid", "TEXT"],
        ["salt", "TEXT"],
        ["keepMsg", "BOOL"],
    ]

    c_contact = [
        ["name", "TEXT"],
        ["uuid", "TEXT"],
    ]

    c_message = [
        ["sender", "TEXT"],
        ["content", "TEXT"],
        ["timestamp", "FLOAT"],  # unix timestamp
        ["group_id", "TEXT"],
    ]

    c_local = [
        ["uuid", "TEXT"],
    ]

    i_local = [uuid.uuid4().hex]

    obj = sqlitewrapper.SqliteCipher(dataBasePath="db/pydatabase.db", checkSameThread=False, password=fp)

    obj.createTable(t_chatroom, c_chatroom, makeSecure=True, commit=True)
    obj.createTable(t_contact, c_contact, makeSecure=True, commit=True)
    obj.createTable(t_message, c_message, makeSecure=True, commit=True)
    obj.createTable(t_local, c_local, makeSecure=True, commit=True)

    obj.insertIntoTable(t_local, i_local, commit=True)
