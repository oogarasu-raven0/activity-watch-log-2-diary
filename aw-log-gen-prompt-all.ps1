[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
$env:PYTHONUTF8=1;
python -m aw_client events aw-watcher-window_DESKTOP-T55UB6B > aw-watcher.log;
python -m aw_client events aw-watcher-afk_DESKTOP-T55UB6B >> aw-watcher.log;
echo "" >> aw-watcher.log;
echo "Android" >> aw-watcher.log;
python -m aw_client events aw-watcher-android-test >> aw-watcher.log;

cp base-prompt.txt aw-prompt.txt
python slim-aw-log.py >> aw-prompt.txt
Add-Type -AssemblyName PresentationCore
[System.Windows.Clipboard]::SetText(
  [System.IO.File]::ReadAllText("aw-prompt.txt", [System.Text.Encoding]::Unicode)
)