from TrustedAuthority import TrustedAuthority
from DataPacket import DataPacket

from random import random, randint, sample
import pdb

class AuthorityNode:
    '''A node with special privileges and powers'''

    def __init__(self, network):
        self.network = network
        self.route_map = {}
        self.dist_map = {}
        self.needs_update = False

    def setup_routes(self):
        for nodeA in self.network.nodes:
            if nodeA.public_key not in self.route_map:
                self.route_map[nodeA.public_key] = {}
                ttl = randint(1, 5)
                cur_ttl = ttl
                self.dist_map[nodeA.public_key] = (ttl, cur_ttl)

            for nodeB in self.network.nodes:
                if nodeA.public_key != nodeB.public_key and \
                   nodeB.public_key not in self.route_map[nodeA.public_key]:

                    ttl = randint(1, 5)  # Making assumption that furthest node is 5 hops
                    cur_ttl = ttl  # Used to keep track of what the current ttl is
                    route = []  # Dummy array that would really hold a route
                    self.route_map[nodeA.public_key][nodeB.public_key] = (ttl, cur_ttl, route)

    def create_cliques(self, N, M):
        n_per_clique = N / M
        start = 0 if N % M == 0 else 1
        cliques = []
        # For simplicity, cliques are uniform
        for i in xrange(start, N, n_per_clique):
            cur_clique = []
            if start and i == 1:
                cur_clique.append(self.network.nodes[0])
            for j in range(i, i+n_per_clique):
                if j < N: cur_clique.append(self.network.nodes[j])
            cliques.append(cur_clique)

        return cliques

    def reroute(self, (source, destination, packet)):
        '''Called when source cannot successfully send a message to 
            the destination node. The authority node will instead try
            to find another route to the final onion destination. This
            rerouting code can be modified as deemed necessary. For example,
            to wait until the destination packet again comes online.'''
        print "\t| Rerouting from %s to %s" % (source.public_key, destination.public_key)

        onion = packet.payload
        onion_dest_key = self.decrypt_onion(onion)
        
        onion_dest = None
        for node in self.network.nodes:
            if node.public_key == onion_dest_key:
                onion_dest = node
                break
        if not onion_dest:
            print "Dropping packet because %s not in network" % (onion_dest_key,)
            self.network.result = -1 if not self.network.result else self.network.result
            return  # The final destination is not in the network. Drop packet.

        # if self.alternate_path(source.public_key, onion_dest.public_key):
            # Onion clique, node, and layer information needs to be moved
            # into the Onion class from the Network class.
        msg = "%s MESSAGE BETWEEN %s AND %s" % (
            onion_dest.public_key, source.public_key, onion_dest.public_key
        )
        new_onion = self.network.construct_onion(source, onion_dest, msg)[0]
        packet = DataPacket(
            length=self.network.packet_length, payload=new_onion, dummy=False
        )
        print "Successfully rerouted packet"
        source.queue_packet(
            onion_dest, packet
        )
        '''
        else:
            # No path exists
        '''
        '''Modify this block to deal with no alternative paths existing.
            For example, you can attempt to find an alternative path
            until some time threshold has elapsed.'''
        # print "Dropping packet because no alternative path exists."

    def alternate_path(self, source, dest):
        '''A finds a path directly to the destination, and
            since A maintains a topology of the network, the route 
            determined by alternate_path is the best possible route
            with the current state of the network. We assume A determines
            this route using the underlying network stack, and simulate
            the results with a random probability.'''
        success_rate = 0.5
        return random() <= success_rate

    '''
    # Pinging is unnecessary because, once initiated, A
    # will receive ping updates from nodes on every timestep.
    # This allows us to make the simplifying adjustment whereby
    # we immediately update A on node additions or deletions, which
    # simulates A receiving information on every timestep. The only
    # risk is that, for the first ttl steps, a connection between A
    # and the corresponding node has yet to be established. We assume
    # that the network can be modified to handle these errors. 
    # In particular, A can be modified to include a ping_node function
    # that expects feedback from the node being pinged within 2*ttl timesteps
    # (1*ttl to reach the node, and 1*ttl to send a message from the node back to A). 
    def ping(self):
        print "pinging"
        for node in self.route_map:
            cur_ttl = self.dist_map[node.public_key][1]

            if cur_ttl == 0:
                exists = self.ping_exists(node.public_key)
                if exists:
                    # Send new ping

                else:
                    # Update cliques, drop from map
                    # Errors may appear in the network until A discovers a dropped or added node
                    self.authority_node.create_cliques(self.network.N, self.network.M)
                    self.authority_node.drop_from_map(dropme)
            else:
                self.dist_map[node.public_key][1] = cur_ttl-1

    def ping_node(self, pub_key):
        pub_keys = [n.public_key for n in self.network.nodes]
        return pub_key in pub_keys
    '''

    def decrypt_onion(self, onion):
        msg = onion.O[0][:]
        secret_dst = msg.strip("~").strip("|").split(" ")[0]

        if secret_dst == '':
            # Message already delivered to target node
            secret_dst = randint(0, len(self.network.nodes)-1)

        return int(secret_dst)

    def add_to_map(self, newnode):
        print "Adding to route_map: " + str(newnode.public_key)
        self.setup_routes()

    def drop_from_map(self, public_key):
        print "Removing %s from route_map" % (public_key,)
        # Remove entry from map
        del self.route_map[public_key]

        # Remove any references to the node 
        for pub_key in self.route_map:
            if public_key in self.route_map[pub_key]:
                del self.route_map[pub_key][public_key]

