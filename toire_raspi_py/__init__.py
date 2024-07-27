import numpy as np
import pyaudio

chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2

threadshold = 0.5

mic = pyaudio.PyAudio()
mic_stream = mic.open(
    format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=chunk
)


def main():
    while True:
        data = mic_stream.read(chunk)
        np_data = np.frombuffer(data, dtype="int16") / 32768.0

        if np.max(np_data) > threadshold:
            print("Detected")


if __name__ == "__main__":
    main()
