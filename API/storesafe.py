import keyring
import codecs
from getpass import getpass

from keyring.core import get_password

class StoreSafe(object):
    """Provides methods to securely store and retrieve passwords from keyring"""

    def __init__(self, service_id:str) -> None:
        super().__init__()
        self.service_id = service_id

    def _set_creds(self, un:str, pw:str):
        hashed = codecs.encode(pw, "rot_13")
        keyring.set_password(self.service_id, "username", un)
        keyring.set_password(self.service_id, "password", hashed)
    
    def _get_creds(self):
        uname = keyring.get_password(self.service_id, "username")
        pword = keyring.get_password(self.service_id, "password")
        if (not uname) or (not pword):
            return None, None
        pword = codecs.decode(pword, "rot_13")
        return uname, pword
    
    def _set_value(self, key, val):
        keyring.set_password(self.service_id, key, val)
    
    def _get_value(self, key):
        return keyring.get_password(self.service_id, key)
    
    def _delete_creds(self):
        keyring.delete_password(self.service_id, "username")
        keyring.delete_password(self.service_id, "password")

if __name__ == "__main__":
    uname = input("username: ")
    pword = input("password: ")
    uac = StoreSafe("Cool.Who")
    print(uac._get_creds())
