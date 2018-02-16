filename = 'hellonet.txt'
chips = 4
cores = [1,3]
neurons = 256
cam_num = 16
connection_type = 0

with open(filename, 'w') as f:
	for neuron in range(neurons):
		if neuron != 0:
			f.write('U01-C01-N{:03d}->{:01d}-{:02d}-U00-C00-N{:03d}\n'.format(neuron, 1, 16, neuron))
			f.write('U02-C02-N{:03d}->{:01d}-{:02d}-U00-C00-N{:03d}\n'.format(neuron, 2, 16, neuron))
			f.write('U03-C03-N{:03d}->{:01d}-{:02d}-U00-C00-N{:03d}\n'.format(neuron, 3, 16, neuron))

print('Network written to {}'.format(filename))
