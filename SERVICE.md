How do make this bad boy run in the background and then just run a command to play a file all the time... 

my one skelly is  C3:93:D4:E0:63:18 for it's Mac address :) 

Yes, the fix is to stop reconnecting for every play. A small background service keeps one Bluetooth connection open and reconnects on its own if it drops. FPP then sends it short “play 1” requests, and each one returns immediately.

I’ve built three files. The idea is a small always-on service that holds one Bluetooth connection to the skelly, with FPP sending it quick play requests.

skelly_daemon.py connects once, keeps the connection open, and reconnects by itself if it drops. It listens on 127.0.0.1:8765 for /play/N, /stop, /volume/N, /status and /wake. If a clip is already playing, /play/N stops it first and then starts it again, so replaying the track works. A request returns right away, so FPP never waits.
skelly_play.sh is the FPP side. skelly_play.sh 1 plays file 1, and skelly_play.sh stop stops it. It logs each result to /home/fpp/media/logs/skelly_play.log.
skelly.service is the systemd unit that starts the daemon at boot and restarts it if it crashes.

Install (over SSH on the Pi)

mkdir -p ~/skelly
# copy skelly_daemon.py into ~/skelly/ and skelly_play.sh into ~/media/scripts/
chmod +x ~/skelly/skelly_daemon.py ~/media/scripts/skelly_play.sh
sudo cp skelly.service /etc/systemd/system/skelly.service
sudo systemctl daemon-reload
sudo systemctl enable --now skelly

Then check it:

journalctl -u skelly -f
~/media/scripts/skelly_play.sh status
~/media/scripts/skelly_play.sh 1

You should see connected in the journal, then the skelly playing file 1. Run skelly_play.sh 1 again as soon as it finishes, or while it’s playing, to test replaying.

FPP playlist: use a Script entry with Script Name skelly_play.sh and Arguments 1, or 2 and so on for other files. Blocking doesn’t matter now, since it returns instantly.

Things to know

One connection only. While the service holds the skelly, the phone app and Chrome page can’t connect. Run sudo systemctl stop skelly before using them, and sudo systemctl start skelly afterwards.
Unconfirmed behavior. I haven’t seen how the skelly responds to a stop and restart, or whether it drops an idle connection after a long time. The service will reconnect if it does, but there may be a few seconds of delay. Tell me what you see in the journal.
Reconnect delay. After a disconnect it takes roughly 3 to 15 seconds to reconnect. A play request during that window waits up to 8 seconds, then fails with an error.
Python path. The unit uses /usr/bin/python3, the same one that worked for you under sudo. If bleak is missing for it, you’ll see a ModuleNotFoundError in the journal.
