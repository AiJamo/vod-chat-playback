# vod-chat-playback
Play back archived streams with chat in a seperate window. Requires Python 3.

Usage: `.\replay.py vod.mp4 vod.log`

![alt text](https://github.com/AiJamo/vod-chat-playback/raw/main/chat_replay.gif)

Currently only supports MPV and chat log files in the format `Timestamp | Username: Message\n` where the timestamp is either a full date in the format `%Y-%m-%d %H:%M:%S` or a `Hours:Minutes:Seconds` timestamp relative to the video. The hours field is optional and the timestamp can be negative for pre-chat. [Chat Downloader](https://github.com/xenova/chat-downloader) outputs in this format if you save as `.log` or `.txt` 

Emojis work if your terminal supports them (Windows Terminal works on Windows, CMD doesn't) Custom channel emotes do not work and I can't see a way to get them working while sticking with the terminal approach. Maybe some day this will have a YouTube-like web based front end.

If your chat log includes pre-chat and uses full date timestamps, you will have to open the script and set the `FIRST_MESSAGE` variable to synchronize the start of the vod with the chat. You can find it near the top of the file. Alternatively, you can just delete all the pre-chat from the log.

Cross-platform *should* work, but it has not been tested and might require minor fixes.
