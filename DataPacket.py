class DataPacket:
    def __init__(self, length, payload, dummy):
        self.length = length
        self.payload = payload
        self.dummy = dummy
