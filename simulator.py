from Network import Network
import pdb

def test_robustness(num_simulations, drop_percentage):
    success, failure = 0, 0
    for i in range(num_simulations):
        manet = Network()
        manet.init()
        result = manet.run(drop_percentage=drop_percentage)
        if result:
            success += 1
        else:
            failure += 1
    return (success, failure, num_simulations)

def test_route_length(num_simulations, mixing_probability, drop_percentage):
    cumulative_length = 0
    for i in range(num_simulations):
        manet = Network()
        manet.init()
        result, length = manet.run(
            drop_percentage=drop_percentage, mixing_probability=mixing_probability
        )
        cumulative_length += length
    return cumulative_length / num_simulations

def run_once():
    manet = Network()
    manet.init()
    result, length = manet.run()
    return result

if __name__=="__main__":
    # run_once()
    # print test_robustness(num_simulations=1, drop_percentage=0.00)
    print test_route_length(num_simulations=1, drop_percentage=0.00, mixing_probability=0.75)
