from TrustedAuthority import TrustedAuthority
from AuthorityNode import AuthorityNode
from DataPacket import DataPacket
from Onion import Onion
from Node import Node

from random import random, randint, sample
import threading
import pdb

class Network:
    """A mobile ad-hoc network"""

    def __init__(self, nodes=[], N=100, cliques=None):
        self.nodes = nodes
        self.N = N
        self.M = 10  # Num pairwise disjoint cliques
        self.cliques = cliques
        self.cover_traffic_rate = 10  # packets/s
        self.real_data_queue = []
        self.packet_length = 50  # bytes
        self.TA = TrustedAuthority()
        self.authority_node = AuthorityNode(self)

        # alpha <= beta <= M
        self.alpha = 3  # Number of onion layers
        self.beta = 8   # Total number of cliques distributed across the layers

        self.result = None
        self.count = 0

    def init(self):
        # Create N nodes
        for n in range(self.N):
            newnode = Node()
            newnode.network = self
            newnode.authority_node = self.authority_node
            self.nodes.append(newnode)

        # 1. Assign nodes into M pairwise disjoint sets
        self.M = 10
        self.beta = randint(self.alpha, self.M)
        self.beta = 3
        self.cliques = self.authority_node.create_cliques(self.N, self.M)
        # self.cliques = self.create_cliques(self.M)

        # 2. Assign node and clique ids, and keys
        self.update_indices()
        self.assign_pub_keys()
        self.assign_priv_keys()
        self.authority_node.setup_routes()

    def run(self, drop_percentage, mixing_probability=0.5):
        # 3. Start cover traffic (per second)
        self.mixing_probability = mixing_probability
        self.drop_percentage = drop_percentage
        self.queue_real_data()
        return self.send_traffic(), self.count

    def add_node(self):
        '''With random probability, add a new node to the network'''
        prob = 0.05
        if random() <= prob:
            self.N += 1
            newnode = Node()
            newnode.network = self
            newnode.authority_node = self.authority_node
            self.nodes.append(newnode)
            self.assign_pub_keys()
            self.assign_priv_keys()
            self.authority_node.create_cliques(self.N, self.M)
            self.authority_node.add_to_map(newnode)

    def drop_node(self):
        '''With random probability, drop a node from the network'''
        prob = 1.0
        if random() <= prob:
            drop_how_many = int(self.drop_percentage * self.N)
            for i in range(drop_how_many):
                self.N -= 1
                node_index = randint(0, len(self.nodes)-1)
                dropme = self.nodes[node_index]

                self.authority_node.create_cliques(self.N, self.M)
                self.authority_node.drop_from_map(dropme.public_key)
                del self.nodes[node_index]

    def node_exists(self, pub_key):
        all_pub_keys = [n.public_key for n in self.nodes]
        return pub_key in all_pub_keys

    # Construct an onion from node SOURCE to DESTINATION
    def construct_onion(self, source, destination, msg):
        onion_layers = {}
        for i in range(self.alpha):
            onion_layers[i+1] = []

        # 1. Choose alpha beta_i's that sum to beta
        betas = [1 for i in range(self.alpha)]
        for i in range(self.beta - self.alpha):
            betas[randint(0, self.alpha-1)] += 1

        # 2. Randomly select beta_i onion cliques for each layer i
        for i, b_i in enumerate(betas):
            chosen_cliques = sample(range(0,len(self.cliques)-1), b_i)
            for index in chosen_cliques:
                onion_layers[i+1].append(self.cliques[index])

        # 3. Check if destination clique was chosen; if not, choose it.
        dest_clique_chosen = False
        for which_layer in onion_layers:
            if onion_layers[which_layer][0][0].clique_id == destination.clique_id:
                dest_clique_chosen = True
                break

        if not dest_clique_chosen:
            which_layer = randint(1, self.alpha)
            which_clique = randint(1, betas[which_layer-1])-1
            onion_layers[which_layer][which_clique] = self.cliques[destination.clique_id]

        # 4. For each onion clique, choose an onion node
        onion_nodes = {}
        dest_layer = 0
        for layer in onion_layers:
            for i, clique in enumerate(onion_layers[layer]):
                clique_id = clique[0].clique_id
                if clique_id == destination.clique_id:
                    onion_node = destination
                    dest_layer = layer
                else:
                    onion_node = clique[randint(0, len(clique)-1)]

                onion_nodes[str(layer) + "," + str(i)] = onion_node

        print "Beta: " + str(self.beta)
        print "Betas: " + str(betas)
        print "Onion nodes:"
        for k in onion_nodes:
            print "\t" + k + ": " + str(onion_nodes[k])
        print "Onion layers:"
        for i, clique in enumerate(onion_layers):
            print "\tlayer " + str(i) + " length: " + str(len(onion_layers[i+1]))
        print "~~~~~~~~~~~~~~ ------------------- ~~~~~~~~~~~~~~~~~"

        # 5. Construct the onion 
        onion = Onion(self, betas, onion_layers, onion_nodes)
        onion.build(msg, dest_layer, self.alpha)

        return (onion, onion_layers, betas)

    def update_indices(self):
        for i, clique in enumerate(self.cliques):
            for j, node in enumerate(clique):
                node.clique_id = i
                node.node_id = j

    def assign_pub_keys(self):
        keys = [n.public_key for n in self.nodes if n.public_key]
        if keys:
            next_key = max(keys) + 1
        else:
            next_key = 0

        for i, node in enumerate(self.nodes):
            if not node.public_key:
                node.public_key = next_key
                next_key += 1

    def assign_priv_keys(self):
        for i, clique in enumerate(self.cliques):
            for j, node in enumerate(clique):
                node.establish_private_key(self.TA)

    def queue_real_data(self):
        # Randomly generate real data between nodes probability % of the time.
        prob = 0.1  # %
        # Markov transition possibility
        for cliqueA in self.cliques:
            for nodeA in cliqueA:
                for cliqueB in self.cliques:
                    for nodeB in cliqueB:
                        # Num messages = threshold * N^2 
                        if nodeA.public_key != nodeB.public_key \
                           and random() <= prob/100:
                            src_node = nodeA
                            dest_node = nodeB
                            msg = "%s MESSAGE BETWEEN %s AND %s" % (dest_node.public_key, src_node.public_key, dest_node.public_key)

                            onion, onion_layers, betas = \
                                    self.construct_onion(src_node, dest_node, msg)
                            packet = DataPacket(
                                length=self.packet_length, payload=onion, dummy=False
                            )
                            src_node.queue_packet(
                                dest_node, packet
                            )
                            return  # Remove this line to create >1 "real" message

    def seed_queue(self):
        src_node = self.nodes[20]
        dest_node = self.nodes[60]
        msg = "MESSAGE BETWEEN %s AND %s" % (src_node.public_key, dest_node.public_key)

        onion, onion_layers, betas = \
                self.construct_onion(src_node, dest_node, msg)
        packet = DataPacket(
            length=self.packet_length, payload=onion, dummy=False
        )
        src_node.queue_packet(
            dest_node, packet
        )

    def send_traffic(self):
        print "Cover traffic"
        self.cover_traffic_rate = 1
        how_often = 1./self.cover_traffic_rate
        threading.Timer(how_often, self.send_traffic).start()

        # Randomly add and drop nodes from the network
        self.add_node()
        self.drop_node()

        # Randomly generate real data for each time step
        # self.queue_real_data()

        # May need to reset data
        # if len(self.real_data_queue) == 0:
        #    self.seed_queue()

        blacklist = [] # A list of which nodes have sent data in this round
        process_limit = len(self.real_data_queue)-1 
        for i, info in enumerate(self.real_data_queue):
            nodeA = info[0]
            nodeB = info[1]
            packet = info[2]

            # Real traffic can go inter- or intra-clique
            if (nodeA, nodeB) not in blacklist:
                # Intra-clique
                nodeA.send_packet(nodeB, packet)
                blacklist.append((nodeA, nodeB))
                self.real_data_queue[i] = "dirty"  # Mark for removal

            # Additions to the queue go beyond the limit,
            # and should only be processed on the next time step
            if i == process_limit:
                break

        # Remove processed data
        self.real_data_queue = [e for e in self.real_data_queue if e != 'dirty']

        # Dummy nodes for the rest of them
        for cliqueA in self.cliques:
            for nodeA in cliqueA:
                for cliqueB in self.cliques:
                    for nodeB in cliqueB:
                        if cliqueA == cliqueB and (nodeA, nodeB) not in blacklist:
                            # Dummy data must only go inter-clique
                            payload = "dummy"
                            dummy_packet = DataPacket(
                                length=self.packet_length, payload=payload, dummy=True
                            )
                            nodeA.send_packet(nodeB, dummy_packet)

        return self.result

