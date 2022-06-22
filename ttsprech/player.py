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


from typing import Optional, Tuple, Type
from types import TracebackType

from threading import Thread
from queue import Queue
import logging
import simpleaudio


logger = logging.getLogger(__name__)


class Player:

    def __init__(self, total: int) -> None:
        self.queue: Queue[Optional[Tuple[str, Optional[str]]]] = Queue()
        self.wave_obj: Optional[simpleaudio.WaveObject] = None
        self.play_obj: Optional[simpleaudio.PlayObject] = None
        self.thread = Thread(target=lambda: self.run())
        self.idx = 0
        self.total = total

    def __enter__(self) -> 'Player':
        self.thread.start()
        return self

    def __exit__(self,  # pylint: disable=useless-return
                 exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> Optional[bool]:
        logger.info("Player shutting down")
        self.queue.put(None)
        self.thread.join()
        return None

    def add(self, text: str, filename: Optional[str]) -> None:
        logger.info(f"Player added {filename} to playlist")
        self.queue.put((text, filename))

    def run(self) -> None:
        logger.info("Player started")

        progress_fmt = f"{{:{len(str(self.total))}d}}"
        while True:
            item = self.queue.get()
            if item is None:
                break

            text, wave_file = item
            self.idx += 1
            print(("[" + progress_fmt + "/" + progress_fmt + "]  {}").format(
                self.idx, self.total, text))

            if wave_file is not None:
                self.wave_obj = simpleaudio.WaveObject.from_wave_file(wave_file)
                self.play_obj = self.wave_obj.play()
                self.play_obj.wait_done()


# EOF #
