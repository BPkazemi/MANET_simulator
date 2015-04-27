from TrustedAuthority import TrustedAuthority
from DataPacket import DataPacket
from Node import Node

from random import random, randint, sample
import threading
import pdb

class Onion:
    ''''An onion, with encrypted message and path'''

    def __init__(self, network, betas, onion_layers, onion_nodes):
        self.network = network
        self.betas = betas
        self.O = []  # <msg, Q_alpha, Q_alpha-1, ..., Q2, Q1>
        self.onion_layers = onion_layers
        self.onion_nodes = onion_nodes
        self.prev_layer = 0

    def __str__(self):
        return "O: %s" % (self.O)

    def build(self, msg, num_layers, alpha):
        '''Encrypts the message and the path alpha number of times'''
        for i in range(num_layers):
            # Num layers encodes num layers to reach destination
            msg += "|"
        for i in range(self.network.alpha - num_layers):
            msg = "~" + msg
        self.O.append(msg)

        path_info = "FLAG"
        for i in range(alpha):
            path_info += "," + str(i+1)  # i+1 = layer
            self.O.insert(1, path_info)

    def peel(self):
        '''Remove one layer of encryption'''
        if self.O[0] != '':
            Q_last = self.O.pop()
            cur_layer = Q_last.split(",")[-1] # 'Decrypt' Q one layer
            if cur_layer.isdigit():
                self.O[0] = self.O[0][:-1]  # Decrypt message one layer

    def get_info(self):
        '''Determine the next onion node, if any, from the current onion.'''
        if self.O[0] == '':
            return -1
        elif self.O[0][-1] in ['|', '~']:
            if self.O[0][-1] == '~' and len(self.O) == 1:
                # Dummy encryption reached
                return -1

            Q_last = self.O[-1]
            cur_layer = Q_last.split(",")[-1]
            return int(cur_layer)
        else:
            message = self.O[0]
            return message
