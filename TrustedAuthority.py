class TrustedAuthority:
    """A trusted authority"""

    def __init__(self):
        self.q = None  # Some large prime
        self.G1 = None  # An additive group of order q
        self.G2 = None  # A multiplicative group of order q
        self.e = None  # A bilinear map of G1 x G1 -> G2

        # self.H = None  # A hash function {0,1}* -> G1*
        # self.master_secret = None  # A master secret kept to itself
        self.H = lambda x: x
        self.master_secret = 12

    def gen_priv_key(self, pub_key):
        return self.master_secret * self.H(pub_key)
