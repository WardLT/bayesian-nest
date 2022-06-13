from abc import ABCMeta, abstractmethod
from csv import DictWriter
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Optional, Union
import logging

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class BaseMonitor(Thread, metaclass=ABCMeta):
    """Base class for threads that monitor the system status"""""

    def __init__(self,
                 name: str,
                 daemon: bool = True,
                 output_path: Optional[Union[Path, str]] = None,
                 write_frequency: float = 600.):
        """Create the thread that will pull the data from the thermostat and store it to disk

        Args:
            name: Name of the service
            daemon: Whether to run this service as a daemon
            output_path: Output path for log files
            write_frequency: How often to write to disk
        """
        super().__init__(daemon=daemon, name=name)
        self.write_frequency = write_frequency

        # Store the path to the log file
        if output_path is None:
            output_path = f'{name}_log.csv'
        self.log_path = Path(output_path)

    @abstractmethod
    def get_log_record(self) -> BaseModel:
        """Get a record of the state of the system

        Returns:
            A record as a JSON-ready BaseModel format
        """
        pass

    def write_log_line(self, status: BaseModel):
        """Append a line to the thermostat log file"""

        # Determine which fields we are writing
        fields = tuple(status.__fields__.keys())

        # Determine whether we need a header
        needs_header = not self.log_path.exists()

        # Write the log data
        with self.log_path.open('a', newline='') as fp:
            writer = DictWriter(fp, fieldnames=fields)
            if needs_header:
                writer.writeheader()
            writer.writerow(status.dict())

    def run(self) -> None:
        """Write to log file as an infinite loop"""
        while True:
            status = self.get_log_record()
            self.write_log_line(status)
            logger.info(f'Successfully updated the {self.name} log')
            sleep(self.write_frequency)
