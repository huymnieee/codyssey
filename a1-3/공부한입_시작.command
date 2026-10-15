#!/bin/zsh
cd -- "${0:A:h}"
python3 -c 'import webbrowser; webbrowser.open("http://127.0.0.1:8003")' &
python3 dev_server.py
