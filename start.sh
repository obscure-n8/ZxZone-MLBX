set -e
python3 update.py
python3 web_server.py &
exec python3 -m bot
