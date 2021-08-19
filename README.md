# vod-chat-playback
Play back archived streams with chat. Requires Python 3.

Currently only supports MPV and chat log files in the format `%Y-%m-%d %H:%M:%S | Username: Message\n`

If your chat log includes pre-chat you will have to open the script and set the `FIRST_MESSAGE` variable to synchronize the start of the vod with the chat. You can find it near the top of the file. Alternatively, you can just delete all the pre-chat from the log. 

Cross-platform *should* work, but has not been tested and might require minor fixes. 
