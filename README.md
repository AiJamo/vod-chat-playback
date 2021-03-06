# vod-chat-playback
Play back archived streams with chat in a seperate window. Requires Python 3.

[Download](https://raw.githubusercontent.com/AiJamo/vod-chat-playback/main/replay.py) (You might have to right click and hit save)

Usage: `replay.py vod.mp4 vod.log` 

![alt text](https://github.com/AiJamo/vod-chat-playback/raw/main/chat_replay.gif)

Currently only supports MPV and chat log files in the format `Timestamp | Username: Message\n` where the timestamp is either a full date in the format `%Y-%m-%d %H:%M:%S` or a `Hours:Minutes:Seconds` timestamp relative to the video. The hours field is optional and the timestamp can be negative for pre-chat. [Chat Downloader](https://github.com/xenova/chat-downloader) outputs in this format if you save as `.log` or `.txt` 

If your chat log includes pre-chat and uses full date timestamps, you will have to open the script and set the `FIRST_MESSAGE` variable to synchronize the start of the vod with the chat. You can find it near the top of the file. Alternatively, you can just delete all the pre-chat from the log.

Emojis work if your terminal supports them (Windows Terminal works on Windows, CMD doesn't) If you are seeing things like ":thumbs_up:" and want it to show up as "👍" instead, run `pip3 install emoji` in a terminal. If you have the emoji package and *don't* want this translation, set the `TRANSLATE_EMOJIS` variable to `False`. Custom channel emotes do not work.

Cross-platform *should* work, but it has not been tested and might require minor fixes.
