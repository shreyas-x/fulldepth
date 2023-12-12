import time
from math import ceil, floor

class ProgressBar:
    START_TIME = 0.0
    RUNTIME = 0.0
    TEXT = ""

    def __init__(self, runtime: (int | float), text: str = "completion") -> None:
        """Creates an instance of the ProgressBar object

        Args:
            runtime (int  |  float): The total run time the loop will be running
            text (str, optional): The text that will be displayed after "Waiting for ", defaults to "completion".
        """        
        self.RUNTIME = runtime
        self.TEXT = text

    def start(self) -> float:
        """Starts the ProgressBar. Saves the start time and returns it to the user.

        Returns:
            float: The output of time.time()
        """        
        self.START_TIME = time.time()
        return self.START_TIME

    def update(self) -> None:
        """Called when the ProgressBar needs to be updated. Usually called after everything is done in the loop.
        
        If you have a time.sleep() call in your loop, it is recommended to call ProgressBar.update() after the time.sleep() call.
        """        
        # elapsed time
        e_time = time.time() - self.START_TIME
        # elapsed percentage from self.RUNTIME
        e_perc = min(100, ceil(e_time/self.RUNTIME * 100))
        # elapsed fraction out of 10
        e_frac = floor(e_perc / 10)

        output = f"\rWaiting for {self.TEXT}: {'█'*e_frac}{'▒'*(10-e_frac)} {e_perc:3.0f}%  "
        print(output, end="")