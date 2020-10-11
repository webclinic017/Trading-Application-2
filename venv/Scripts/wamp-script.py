#!C:\Users\win10\PycharmProjects\Trading-Application\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'autobahn==19.10.1','console_scripts','wamp'
__requires__ = 'autobahn==19.10.1'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('autobahn==19.10.1', 'console_scripts', 'wamp')()
    )
