class Phase_manager:
    def __init__(self, broadcast):
        self.broadcast = broadcast

    def set_phase(self, phase):
        self.phase = phase
        # and then tell the phase to every client
        self.broadcast(f"\nPhase is {phase}")
    # to make it day

    def set_day(self):
        self.set_phase("DAY")
    # to make it night

    def set_night(self):
        self.set_phase('NIGHT')
