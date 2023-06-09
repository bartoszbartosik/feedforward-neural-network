import json
import sys
from typing import List, Callable

import matplotlib.pyplot as plt
import numpy as np

from neuralnetwork.layer import Layer


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # #   S T A T I C   F U N C T I O N S   # # # # # # # # # # # # # # # # # # # #
def sigmoid(x):
    return 1/(1+np.exp(-x))


# Rectified Linear Unit
def relu(x):
    if x <= 0:
        return 0
    else:
        return x

# Return derivative value of a given function in a given point
def derivative(function: Callable, x: np.ndarray):
    if function.__name__ == 'sigmoid':
        return function(x)*(1-function(x))
    elif function.__name__ == 'relu':
        if x <= 0:
            return 0
        else:
            return 1


class FeedforwardNeuralNetwork:

    def __init__(self):


        # INITIALIZE LAYERS
        self.layers: List[Layer] = []


    def add_layer(self, neurons_number: int, activation_function: str):
        """
        Add new layer with consisting of given number of neurons and their activation function.
        """
        function = None
        if activation_function == 'sigmoid':
            function = sigmoid
        elif activation_function == 'relu':

            function = relu

        if len(self.layers) == 0:
            self.layers.append(Layer(input_array=np.empty(neurons_number),
                                     neurons_number=neurons_number,
                                     activation_function=relu))
        else:
            self.layers.append(Layer(input_array=self.layers[-1].toarray(),
                                     neurons_number=neurons_number,
                                     activation_function=function))


    def train(self, training_data, epochs, learning_ratio, plot_cost=False, plot_accuracy=False, discretize_accuracy=False):
        """
        Train the Neural Network.
        """
        total_costs = []
        accuracy = []
        for i in range(epochs):
            for input_data, output_data in zip(training_data[0], training_data[1]):
                self.feedforward(input_data)
                self.sgd(output_data, learning_ratio)

            # Progress bar
            sys.stdout.write('\r')
            sys.stdout.write("Training in progress: [%-20s] %d%%" % ('=' * int(i/epochs*20), int(i/epochs*100)))
            sys.stdout.flush()

            if plot_cost:
                total_costs.append(self.total_cost(training_data))
            if plot_accuracy:
                accuracy.append(self.accuracy(training_data, discretize_accuracy))

        if plot_cost or plot_accuracy:
            if plot_cost:
                plt_cost = plt.figure()
                ax_cost = plt_cost.add_subplot(111)
                ax_cost.plot(range(1, epochs+1), total_costs, color='0.3')
                ax_cost.set_title('COST FUNCTION ERROR')
                ax_cost.set_xlabel('epoch')
                ax_cost.set_ylabel('cost function')
                ax_cost.grid()

            if plot_accuracy:
                plt_accuracy = plt.figure()
                ax_accuracy = plt_accuracy.add_subplot(111)
                ax_accuracy.plot(range(1, epochs+1), accuracy, color='0.3')
                ax_accuracy.set_title('ACCURACY')
                ax_accuracy.set_xlabel('epoch')
                ax_accuracy.set_ylabel('accuracy')
                ax_accuracy.grid()

            plt.show()


    def predict_output(self, input_data):
        """
        Predict output of a neural network for a given input
        """
        self.feedforward(input_data)
        return self.layers[-1].toarray()


    def feedforward(self, input_data):
        for neuron, new_input in zip(self.layers[0].neurons, input_data):
            neuron.value = new_input
        for i in range(1, len(self.layers)):
            self.layers[i].input_array = self.layers[i - 1].toarray()
            self.layers[i].feedforward()


    def total_cost(self, training_data):
        """
        Return total average cost function value for all the training data
        """
        # Initialize error array
        errors = []

        # Calculate error for each training data
        for input_data, output_data in zip(training_data[0], training_data[1]):
            # Pass the input data to the neural network
            self.feedforward(input_data)

            # Get the outcome of the above
            actual_output = self.layers[-1].toarray()

            # Compare it with the expected outcome
            error: np.ndarray = (actual_output - output_data)**2/2

            # Append it to array error
            errors.append(error)

        errors = np.mean(np.array(errors), axis=0)
        errors = np.sum(errors)

        return errors


    def accuracy(self, training_data, discretize):
        """
        Compute percentage of correct Neural Network's predictions of the training data.
        """
        correct_results = 0
        total = len(training_data[0])
        for input_data, output_data in zip(training_data[0], training_data[1]):
            # Pass the input data to the neural network
            self.feedforward(input_data)

            if discretize:
                # Actual output
                actual_output = np.round(self.layers[-1].toarray())
                # Expected output
                expected_output = output_data
            else:
                # Actual output
                actual_output = np.argmax(self.layers[-1].toarray())
                # Expected output
                expected_output = np.argmax(output_data)

            if actual_output == expected_output:
                correct_results += 1

        return correct_results/total


    def backpropagation(self, output_data):
        """
        Calculate the Cost Function derivative over each weight and bias in order to determine its gradient.

        OUTPUT LAYER
        MAIN EQUATION
        d(C_{tot}) / d(w_{L}) = d(C_{tot})/d(a_{L}) * d(a_{L})/d(z_{L}) * d(z_{L})/d(w_{L})

        Simplified
        dc_dw = dc_da * da_dz * dz_dw

        PARTIAL DERIVATIVES
        d(C_{tot})/d(a_{L}) = a_{L} - expected_output
        d(a_{L})/d(z_{L}) = d(activation_function(z_{L}))/d(weights)
        d(z_{L})/d(w_{L}) = a_{L-1}
        """

        # Initialize Cost Function gradient with respect to the weights' matrix
        grad_w = []

        # Initialize Cost Function gradient with respect to the biases' matrix
        grad_b = []

        # Calculate both gradients for all layers:
        for l in range(-1, -len(self.layers), -1):
            # Initialize input values of each neuron in current layer
            inputs_l = self.layers[l].get_inputs()

            # Get the current layer's values
            outputs_l = self.layers[l].toarray()

            # Get the previous layer's values
            outputs_l_prev = self.layers[l-1].toarray()

            # Get the current layer's activation function
            activation_function = self.layers[l].activation_function

            # CALCULATE ERROR IN THE L-TH LAYER
            # Output layer
            if l == -1:
                # Error in the given layer
                d_l = ((outputs_l - output_data) * derivative(activation_function, inputs_l))
                dc_dw = np.outer(outputs_l_prev, d_l)
            # Hidden layers
            else:
                # Initialize error array in the given layer
                d_l_temp = []
                # Find error of each neuron in the given layer and append it to the layer errors
                for neuron_index in range(self.layers[l].neurons.size):
                    w_previous = [neuron.weights[neuron_index] for neuron in self.layers[l + 1].neurons]
                    d_l_temp.append(np.dot(w_previous, grad_b[-1]))
                d_l = np.array(d_l_temp).flatten()

                # Calculate cost function over weight derivative
                dc_dw = np.outer(outputs_l_prev, d_l * derivative(sigmoid, inputs_l))

            # Add results to the gradient vectors
            grad_w.append(dc_dw)
            grad_b.append(d_l)

        return grad_w, grad_b

    def sgd(self, output_data: np.ndarray, learning_rate):
        """
        Update the weights and biases using backpropagation and Stochastic Gradient Descent.
        """

        # Calculate the Cost Function gradient with respect to the weights and biases
        grad_w, grad_b = self.backpropagation(output_data)

        # Initialize new weights and biases arrays
        w_new = []
        b_new = []

        # Compute new weights and biases using Stochastic Gradient Descent
        for i in range(-1, -len(self.layers), -1):
            w_old = self.layers[i].get_weights()
            b_old = self.layers[i].get_biases()

            w_new.append(w_old - learning_rate*grad_w[-i-1].transpose())
            b_new.append(b_old - learning_rate*grad_b[-i-1].transpose())

            for index, neuron in enumerate(self.layers[i].neurons):
                neuron.weights = w_old[index] - learning_rate*grad_w[-i-1].transpose()[index]
                neuron.bias = b_old[index] - learning_rate*grad_b[-i-1].transpose()[index]


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # # # # #   S A V E   &   L O A D   # # # # # # # # # # # # # # # # # # # # # #

    def save_network(self, filename, filepath = 'saved/'):
        """
        Save current Neural Network's architecture.
        """
        network = {
            'layers': [(layer.size, layer.activation_function.__name__) for layer in self.layers],
            'weights': [layer.get_weights().tolist() for layer in self.layers[1:]],
            'biases': [layer.get_biases().tolist() for layer in self.layers[1:]]
        }

        file = open('{}{}.json'.format(filepath, filename), 'w')
        json.dump(network, file)
        file.close()

    def load_network(self, filename, filepath = 'saved/'):
        """
        Load and overwrite Neural Network from a given file.
        """
        file = open('{}{}.json'.format(filepath, filename), 'r')
        network = json.load(file)
        file.close()

        layers = network['layers']

        weights = network['weights']
        biases = network['biases']

        self.layers.clear()
        for size, activation_function in layers:
            self.add_layer(size, activation_function)


        for layer, weights_l, biases_l in zip(self.layers[1:], weights, biases):
            for neuron, weight, bias in zip(layer.neurons, weights_l, biases_l):
                neuron.weights = weight
                neuron.bias = bias



    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # # # #   V I S U A L I Z A T I O N   # # # # # # # # # # # # # # # # # # # # #
    def visualize(self):
        pass


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # #   P R I V A T E   F U N C T I O N S   # # # # # # # # # # # # # # # # # # #


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # #   O V E R W R I T T E N   F U N C T I O N S   # # # # # # # # # # # # # # # # #
    def __str__(self) -> str:
        return 'ANN: [Layers: {}]'.format([str(layer) for layer in self.layers])


    def __repr__(self):
        return self.__str__()
