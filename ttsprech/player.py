# ttsprech - Simple text to wav for the command line
# Copyright (C) 2022 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from threading import Thread
import logging
import simpleaudio
import queue


logger = logging.getLogger(__name__)


class Player:

    def __init__(self) -> None:
        self.queue = queue.Queue()
        self.wave_obj = None
        self.play_obj = None
        self.thread = Thread(target=lambda: self.run())

    def __enter__(self) -> 'Player':
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        logger.info(f"Player shutting down")
        self.queue.put(None)
        self.thread.join()

    def add(self, filename: str) -> None:
        logger.info(f"Player added {filename} to playlist")
        self.queue.put(filename)

    def run(self):
        logger.info(f"Player started")
        while True:
            wave_file = self.queue.get()
            if wave_file is None:
                break
            self.wave_obj = simpleaudio.WaveObject.from_wave_file(wave_file)
            self.play_obj = self.wave_obj.play()
            self.play_obj.wait_done()


# EOF #
