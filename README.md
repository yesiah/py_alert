Example of a valid secrets.py, using macOS Keychain and python keyring.

```
# Keyring
import keyring
import keyring.backends.macOS

def get_gmail_account():
  return 'best_email_address@gmail.com'

def get_gmail_pw():
  keyring.set_keyring(keyring.backends.macOS.Keyring())
  return keyring.get_password('system', 'username')
```