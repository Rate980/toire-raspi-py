import os
import wave

import numpy as np
import pyaudio
import serial
from dotenv import load_dotenv

load_dotenv()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 2

threadshold = 0.5


class SeirialPort:
    def __init__(self, path: str):
        self.serial_port = serial.Serial(path, 115200, timeout=1)

    def send_on_unko(self):
        self.serial_port.write(b"0")

    def send_on_clean(self):
        self.serial_port.write(b"1")

    def send_on_cleaning_done(self):
        self.serial_port.write(b"2")

    def send_reset(self):
        self.serial_port.write(b"3")


class MicStream:
    def __init__(self, sound: list[bytes], serial_port: SeirialPort):
        serial_port.send_reset()
        self.serial_port = serial_port
        self.sound = sound
        self.audio_index = 0
        self.exist_unko = False
        self.is_playing = False
        self.pyaudio = pyaudio.PyAudio()
        self.playinddex = 0
        self.stream = self.pyaudio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=True,
            frames_per_buffer=CHUNK,
            stream_callback=self.callback,
        )

    def callback(self, in_data, frame_count, time_info, status):
        self.callback_input(in_data, frame_count, time_info, status)
        data = self.callback_output(in_data, frame_count, time_info, status)
        if data is None:
            data = b"\x00" * 4096
        return (data, pyaudio.paContinue)

    def callback_input(self, in_data, frame_count, time_info, status):
        if not self.is_read:
            return

        data = in_data
        np_data = np.frombuffer(data, dtype="int16") / 32768.0

        if np.max(np_data) > threadshold:
            print("Detected")
            self.play()
            self.serial_port.send_on_clean()

    def callback_output(self, in_data, frame_count, time_info, status):
        if not self.is_playing:
            return

        if self.audio_index >= len(self.sound):
            self.on_endplay()
            return

        data = self.sound[self.audio_index]
        self.audio_index += 1
        return data

    def on_unko(self):
        self.exist_unko = True
        if not self.is_playing:
            self.serial_port.send_on_unko()

    def on_endplay(self):
        print("End play")
        self.is_playing = False
        self.serial_port.send_on_cleaning_done()
        if self.exist_unko:
            self.serial_port.send_on_unko()

    @property
    def is_read(self):
        return self.exist_unko and not self.is_playing

    def play(self):
        self.audio_index = 0
        self.is_playing = True
        self.exist_unko = False


def main():
    sound = wave.open("toire_raspi_py/sound.wav", "r")
    sounds: list[bytes] = []
    while True:
        data = sound.readframes(CHUNK)
        if data == b"":
            break
        sounds.append(data)

    serial_port = SeirialPort(os.environ["SERIAL_PATH"])

    mic_stream = MicStream(sounds, serial_port)
    while True:
        input("Press Enter to send unko")
        mic_stream.on_unko()


if __name__ == "__main__":
    main()
