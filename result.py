import matplotlib.pyplot as plt

success_rate = [10./10., 10./10., 9./10., 9./10., 8./10.]
num_kickbacks = [0./10., 8./10., 8./10., 9./10., 9./10.]
num_dropped = [0./10., 4./10., 5./10., 8./10., 9./10.]

x = [0, 0.2, 0.35, 0.5, 0.6]

plt.plot(x, num_dropped, 'ro-')
plt.axis([0., 1., 0., 1.5])
plt.xlabel('% network removed')
plt.ylabel('% of onions ultimately dropped')
plt.show()
