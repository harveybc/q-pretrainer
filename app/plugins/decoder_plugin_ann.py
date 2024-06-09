import numpy as np
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.optimizers import Adam

class Plugin:
    """
    A simple neural network-based decoder using Keras, with dynamically configurable size.
    """

    plugin_params = {
        'encoding_dim': 32,
        'output_dim': None,
        'epochs': 50,
        'batch_size': 256
    }

    plugin_debug_vars = ['encoding_dim', 'output_dim', 'epochs', 'batch_size']

    def __init__(self):
        self.params = self.plugin_params.copy()
        self.model = None

    def set_params(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.params:
                self.params[key] = value

    def get_debug_info(self):
        return {var: self.params[var] for var in self.plugin_debug_vars}

    def add_debug_info(self, debug_info):
        plugin_debug_info = self.get_debug_info()
        debug_info.update(plugin_debug_info)

    def configure_size(self, encoding_dim, output_dim):
        self.params['encoding_dim'] = encoding_dim
        self.params['output_dim'] = output_dim

        self.model = Sequential([
            Dense(int(encoding_dim * 2), input_shape=(encoding_dim,), activation='relu'),
            Dense(output_dim, activation='sigmoid')
        ])
        self.model.compile(optimizer=Adam(), loss='mean_squared_error')

    def train(self, encoded_data, original_data):
        self.model.fit(encoded_data, original_data, epochs=self.params['epochs'], batch_size=self.params['batch_size'], verbose=0)

    def decode(self, encoded_data):
        return self.model.predict(encoded_data)

    def save(self, file_path):
        self.model.save(file_path)

    def load(self, file_path):
        self.model = load_model(file_path)

    def calculate_mse(self, original_data, reconstructed_data):
        return np.mean(np.square(original_data - reconstructed_data))
