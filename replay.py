import subprocess, time, os, uuid, atexit, json, datetime, re, threading, queue, sys, io

FIRST_MESSAGE = None
# Used for synchronizing the chat log to the video in the case that there is pre-stream in the log
# Opening the log in a text editor and finding the guy saying "refresh" seems to work if you subtract a few seconds to account for his reaction time
# If there is no pre-stream chat in the log you can keep this None, otherwise something like FIRST_MESSAGE = "2021-08-17 20:06:20"

MPV_PATH = r"mpv" # Write your full MPV path here if it's not in PATH
SMOOTH_CHAT = True # Buffers a second of chat to feed it out smoothly instead of in big chunks
HIDE_USERNAMES = True # Helps unclutter the chat and make use of horizontal room
BUFFER_LOGFILE = True # Big responsiveness gains and much more efficient disk access. Only disable if you can't afford the memory to load the entire chat log at once.

class MPV: # Used the Syncplay source as a reference for how to communicate with MPV
    def __init__(self, exe_path, media=None):
        self.pipe_path = "mpvpipe-{}".format(uuid.uuid4().hex)
        if os.name == "nt": self.pipe_path = "\\\\.\\pipe\\" + self.pipe_path
        if media is None: self.process = subprocess.Popen([exe_path, "--input-ipc-server={}".format(self.pipe_path)])
        else: self.process = subprocess.Popen([exe_path, media, "--input-ipc-server={}".format(self.pipe_path)])
        atexit.register(self.destroy)

        for _ in range(30):
            time.sleep(0.1)
            self.process.poll()
            if os.path.exists(self.pipe_path):
                break
        else:
            raise ValueError("MPV failed to start")

        time.sleep(0.1) # Seems to solve a semi-random OSError
        self.pipe = open(self.pipe_path, "rb+", buffering=0)

    def write(self, command):
        self.pipe.write(command)

    def read(self):
        command = b""
        cur = self.pipe.read(1)
        while cur != b"\n":
            command += cur
            cur = self.pipe.read(1)
        return json.loads(command.decode("utf8"))

    def destroy(self):
        self.process.terminate()
        if hasattr(self, "pipe"): self.pipe.close()
        if os.name != "nt":
            try:
                os.remove(self.pipe_path)
            except FileNotFoundError:
                pass

class Log:
    def __init__(self, path, first=None):
        if BUFFER_LOGFILE:
            self.log_file = io.StringIO()
            with open(path, "r", encoding="utf8") as log_file:
                self.log_file.write(log_file.read())
            self.log_file.seek(0)
        else:
            self.log_file = open(path, "r", encoding="utf8")
        self.last_offset = 0
        self.last_start = 0
        self.next_at = None

        if first is None:
            self.seeking = False
            self.first = None
        else:
            self.first = first
            self.seeking = True

    def seek(self):
        self.seeking = True
        self.next_at = None

    def next_message(self):
        self.last_start = self.log_file.tell()
        line = self.log_file.readline().strip()
        if self.log_file.tell() == self.last_start: return None # Out of log
        if "|" not in line: return self.next_message()

        offset = time.mktime(datetime.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S").timetuple())
        if self.first is None: self.first = offset
        offset = offset - self.first
        return (offset, line[22:])

    def rewind(self):
        self.log_file.seek(self.last_start)

    def new_messages(self, target_offset):
        if self.seeking and target_offset < self.last_offset:
            self.log_file.seek(0) # Rewind the file if the skip was backwards

        if self.next_at is not None and self.next_at > target_offset: return [] # We know when the next message should appear and it is not now

        out = []
        while True:
            next_message = self.next_message()
            if next_message is None: break # Out of log no message could be read
            timestamp, message = next_message
            if timestamp > target_offset: # Message is from the future
                self.next_at = timestamp
                self.rewind() # Put it back where it came from
                break
            if self.seeking: # Prevents output of any of the chat messages it goes through while catching up to a seek
                if SMOOTH_CHAT and target_offset - timestamp <= 1: self.seeking = False # Stop seeking a second early to fill up the buffer if smooth chatting
                else: continue
            if ":" not in message: continue # Superchat or something
            if HIDE_USERNAMES: message = re.sub(r"^.*: ", "", message)
            out.append(message)

        self.seeking = False
        self.last_offset = target_offset
        return out

def get_messages(queue, video, chat_log, first_message):
    if first_message is not None: first = time.mktime(datetime.datetime.strptime(first_message[:19], "%Y-%m-%d %H:%M:%S").timetuple())
    else: first = None
    log = Log(chat_log, first)
    mpv = MPV(MPV_PATH, video)
    global playing # *Should* be thread safe enough

    while not die:
        input = mpv.read()
        if input.get("event") == "property-change" and input.get("name") == "playback-time" and "data" in input:
            playing = True
            offset = input.get("data")
            for message in log.new_messages(offset):
                queue.put(message)
        elif input.get("event") == "seek":
            with queue.mutex:
                queue.queue.clear()
            log.seek()
        elif input.get("event") == "end-file":
            break
        elif input.get("event") == "playback-restart":
            mpv.write(b'{ "command": ["observe_property", 1, "playback-time"] }\n')
        elif input.get("event") == "pause":
            playing = False
        elif input.get("event") == "unpause":
            playing = True

if len(sys.argv) < 3:
    print("Usage: {} video log".format(sys.argv[0]))
    print("Example: {} gura.mp4 gura.log".format(sys.argv[0]))
    exit()
video = sys.argv[1]
if not os.path.exists(video):
    print("Can't find video file \"{}\"".format(video))
    exit()
chat_log = sys.argv[2]
if not os.path.exists(chat_log):
    print("Can't find chat log file \"{}\"".format(chat_log))
    exit()

playing = True
die = False
message_queue = queue.Queue()
worker = threading.Thread(target=get_messages, args=(message_queue, video, chat_log, FIRST_MESSAGE))
worker.setDaemon(True)
worker.start()
while worker.is_alive():
    try:
        if playing:
            try:
                message = message_queue.get(block=False)
                message_queue.task_done()
                print(message)
                if SMOOTH_CHAT:
                    qsize = message_queue.qsize()
                    if qsize > 0: time.sleep(1/qsize)
                    else: time.sleep(1)
            except queue.Empty:
                if SMOOTH_CHAT: time.sleep(1)
                else: time.sleep(0.017)
        else:
            time.sleep(0.017)
    except KeyboardInterrupt:
        break
die = True
worker.join(1)
