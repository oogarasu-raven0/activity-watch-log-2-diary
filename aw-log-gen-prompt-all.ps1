[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
$env:PYTHONUTF8=1;
$server = "http://localhost:5600"

python download-bucket-from-google-drive.py;

curl.exe -X DELETE $server/api/0/buckets/aw-stopwatch;
curl.exe -X DELETE $server/api/0/buckets/aw-watcher-android-test;
curl.exe -X DELETE $server/api/0/buckets/aw-watcher-android-unlock;
curl.exe -X DELETE $server/api/0/buckets/aw-watcher-android-web-chrome;

curl.exe -H "Content-Type: application/json" --data-binary "@buckets.json" $server/api/0/import;

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

rm aw-watcher.log
rm buckets.json