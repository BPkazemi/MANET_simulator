from DataPacket import DataPacket
from random import random, randint
from AuthorityNode import AuthorityNode
import pdb
import copy

def deepcopy_with_sharing(obj, shared_attribute_names, memo=None):
    '''
    Deepcopy an object, except for a given list of attributes, which should 
    be shared between the original object and its copy.
    
    obj is some object
    shared_attribute_names: A list of strings identifying the attributes that
    should be shared between the original and its copy.
    memo is the dictionary passed into __deepcopy__.  Ignore this argument if 
    not calling from within __deepcopy__.
    '''
    
    assert isinstance(shared_attribute_names, (list, tuple))
    shared_attributes = {k: getattr(obj, k) for k in shared_attribute_names}
    
    if hasattr(obj, '__deepcopy__'):
        # Do hack to prevent infinite recursion in call to deepcopy
        deepcopy_method = obj.__deepcopy__
        obj.__deepcopy__ = None
        
    for attr in shared_attribute_names:
        del obj.__dict__[attr]
        
    clone = copy.deepcopy(obj, memo)
    
    for attr, val in shared_attributes.iteritems():
        setattr(obj, attr, val)
        setattr(clone, attr, val)
        
    if hasattr(obj, '__deepcopy__'):
        # Undo hack
        obj.__deepcopy__ = deepcopy_method
        
    return clone

class Node:
    """A MANET node"""
    def __init__(self):
        self.q = None
        self.G1 = None
        self.G2 = None
        self.e = None
        self.H = None
        self.authority_node = None

        self.clique_id = None
        self.node_id = None 

        self.public_key = None  # Network id
        self.private_key = None  # Obtained from TA

        self.received_data = []
        self.network = None

    def receive_packet(self, from_who, packet):
        self.received_data.append((from_who, packet))
        if type(packet.payload) != str:
            # Onion, queue it
            self.queue_packet(from_who, packet)

    def queue_packet(self, from_who, packet):
        if type(packet.payload) == str:
            # Dummy cover traffic
            # receiving_node = self.network.cliques[clique_id][node_id]
            receiving_node = from_who 
            self.network.real_data_queue.append((self, receiving_node, packet))
        else:
            # An onion's next node is randomly determined 
            # according to a mixing probability
            if random() <= self.network.mixing_probability:
                # print "Randomizing what should've been between %s and %s" \
                #        % (from_who.public_key, self.public_key)

                # 1. Pick random node in same clique as sender
                same_clique = self.network.cliques[from_who.clique_id]

                # Possible infinite loop if cliques are of size 1
                # Make sure cliques have >1 node
                rand_i = randint(0, len(same_clique)-1)
                rand_node = same_clique[rand_i]
                while rand_node.public_key == from_who.public_key:
                    rand_i = randint(0, len(same_clique)-1)
                    rand_node = same_clique[rand_i]

                # 2. Queue it. Note that we leave the onion untouched
                receiving_node = rand_node
                self.network.count += 1
                print "RANDOM from %s to %s" % (from_who.public_key, receiving_node.public_key)
                if self.network.node_exists(receiving_node.public_key):
                    self.network.real_data_queue.append((self, receiving_node, packet))
                else:
                    print "Coming from a random mix"
                    self.authority_node.reroute((self, receiving_node, packet))
            else:
                # Otherwise, peel it and queue it.
                onion = packet.payload
                if not hasattr(onion, 'O'):
                    pdb.set_trace()
                print "\t- onion.O: " + str(onion.O)
                info = onion.get_info()
                if type(info) == str:
                    # Get the message body from the encrypted string
                    message = info 
                    while message[0] == '~':
                        message = message[1:]

                    print "Message: " + message
                    self.network.result = 1

                    # Remove the message from the path object
                    onion.O[0] = ''.join(
                        [c for c in onion.O[0] if c == '~']
                    )
                    cur_layer = onion.prev_layer + 1
                    onion.prev_layer += 1
                else:
                    cur_layer = info
                    if cur_layer == -1:
                        return  # The onion can no longer be decrypted
                    onion.prev_layer = cur_layer

                # Occasionally happens
                if cur_layer > len(onion.onion_layers):
                    return

                dest_cid = from_who.clique_id
                dest_nid = from_who.node_id

                # Queue data for each real onion node per layer
                # because fake ones cannot source data
                print "Cur_layer: " + str(cur_layer) 
                if not packet.dummy:
                    for clique_num, clique in enumerate(onion.onion_layers[cur_layer]):
                        onion_node = onion.onion_nodes[str(cur_layer) + "," + str(clique_num)]
                        print "Receiving node: " + str(onion_node) 
                        print "\tSender: " + str(self)

                        onion_copy = deepcopy_with_sharing(onion, ['onion_nodes'])
                        onion_copy.peel()
                        print "\t- peeledO: " + str(onion_copy.O)
                        dummy = False if clique_num == 0 else True
                        packet = DataPacket(
                            length=packet.length, payload=onion_copy, dummy=dummy
                        )

                        receiving_node = onion_node
                        self.network.count += 1
                        if self.network.node_exists(receiving_node.public_key):
                            self.network.real_data_queue.append((self, receiving_node, packet))
                        else:
                            print "Coming from a determined route"
                            self.authority_node.reroute((self, receiving_node, packet))

    def send_packet(self, to_whom, payload):
        # Sending a packet should route through the network,
        # but exactly how depends on the routing layer and those 
        # details are not relevant here. The below will suffice.
        to_whom.receive_packet(self, payload)

    def establish_private_key(self, TA):
        self.private_key = TA.gen_priv_key(self.public_key)

    def establish_shared_key(self, nodeB):
        # e is a modified Weil & Tate pairing. Details not important
        # return self.e(self.private_key, self.H(nodeB))
        return self.private_key + nodeB.private_key # Dummy

    def generate_pseudonym(self):
        r = randint(-999999, 999999)
        # return r * self.H(self)
        return r * self.public_key

    def __str__(self):
        return "clique_id: %s, node_id: %s, public_key: %s" % (
            self.clique_id, self.node_id, self.public_key
        )
