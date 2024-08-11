import numpy as np
from keras.models import Sequential, load_model
from keras.layers import Dense, Conv1D, UpSampling1D, Reshape, Flatten, Conv1DTranspose,Dropout
from keras.optimizers import Adam
from tensorflow.keras.initializers import GlorotUniform, HeNormal

from keras.regularizers import l2
from keras.callbacks import EarlyStopping
from keras.layers import BatchNormalization, MaxPooling1D, Cropping1D
import math

class Plugin:
    plugin_params = {
        'intermediate_layers': 3, 
        'learning_rate': 0.001,
        'dropout_rate': 0.01,
    }

    plugin_debug_vars = ['interface_size', 'output_shape', 'intermediate_layers']

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

    def configure_size(self, interface_size, output_shape):
        self.params['interface_size'] = interface_size
        self.params['output_shape'] = output_shape

        layer_sizes = []

        # Calculate the sizes of the intermediate layers
        num_intermediate_layers = self.params['intermediate_layers']
        layers = [output_shape]
        step_size = (output_shape - interface_size) / (num_intermediate_layers + 1)
        
        for i in range(1, num_intermediate_layers + 1):
            layer_size = output_shape - i * step_size
            layers.append(int(layer_size))

        layers.append(interface_size)

        # For the decoder, reverses the order of the generted layers.
        layer_sizes=layers
        layer_sizes.reverse()
        
        # Debugging message
        print(f"Decoder Layer sizes: {layer_sizes}")
       




        self.model = Sequential(name="decoder")

        # 1. Dense layer to start the decoding process
        self.model.add(Dense(layer_sizes[0], input_shape=(interface_size,), activation='relu', kernel_initializer=HeNormal(), name="decoder_in"))
        self.model.add(BatchNormalization())
        self.model.add(Reshape((layer_sizes[0], 1)))
        print(f"After Reshape: {self.model.layers[-1].output_shape}")
        upsample_factor = math.ceil(output_shape / layer_sizes[0])
        if upsample_factor > 1:
            self.model.add(UpSampling1D(size=upsample_factor))
        print(f"After UpSampling1D: {self.model.layers[-1].output_shape}")
        
        # 3. Continue with Conv1DTranspose layers
        for size in layer_sizes:
            kernel_size = 3 if size <= 64 else 5 if size <= 512 else 7
            self.model.add(Conv1DTranspose(filters=size, kernel_size=kernel_size, padding='same', activation='relu', kernel_initializer=HeNormal(), kernel_regularizer=l2(0.01)))
            print(f"After Conv1DTranspose (filters={size}): {self.model.layers[-1].output_shape}")
            self.model.add(BatchNormalization())
            print(f"After BatchNormalization: {self.model.layers[-1].output_shape}")
            # Upsample the output to match the next layer size
  
            self.model.add(Dropout(self.params['dropout_rate'] / 2))
            print(f"After Dropout: {self.model.layers[-1].output_shape}")

        # 5. Fine-tune to exact output size if necessary
        #self.model.add(Conv1DTranspose(output_shape, kernel_size=kernel_size, padding='same', activation='relu', kernel_initializer=HeNormal(), name="last_layer"))
        last_layer_shape = self.model.layers[-1].output_shape
        new_shape = (last_layer_shape[2], last_layer_shape[1])
        self.model.add(Reshape(new_shape))
        self.model.add(Conv1DTranspose(1, kernel_size=3, padding='same', activation='tanh', kernel_initializer=GlorotUniform(), name="decoder_output"))
        print(f"Final Output Shape: {self.model.layers[-1].output_shape}")







                # Define the Adam optimizer with custom parameters
        adam_optimizer = Adam(
            learning_rate= self.params['learning_rate'],   # Set the learning rate
            beta_1=0.9,            # Default value
            beta_2=0.999,          # Default value
            epsilon=1e-7,          # Default value
            amsgrad=False          # Default value
        )

        self.model.compile(optimizer=adam_optimizer, loss='mean_squared_error')

    def train(self, encoded_data, original_data):
        encoded_data = encoded_data.reshape((encoded_data.shape[0], -1))
        original_data = original_data.reshape((original_data.shape[0], -1))
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        self.model.fit(encoded_data, original_data, epochs=self.params['epochs'], batch_size=self.params['batch_size'], verbose=1, callbacks=[early_stopping])

    def decode(self, encoded_data):
        encoded_data = encoded_data.reshape((encoded_data.shape[0], -1))
        decoded_data = self.model.predict(encoded_data)
        decoded_data = decoded_data.reshape((decoded_data.shape[0], -1))
        return decoded_data

    def save(self, file_path):
        self.model.save(file_path)

    def load(self, file_path):
        self.model = load_model(file_path)

    def calculate_mse(self, original_data, reconstructed_data):
        original_data = original_data.reshape((original_data.shape[0], -1))
        reconstructed_data = reconstructed_data.reshape((original_data.shape[0], -1))
        mse = np.mean(np.square(original_data - reconstructed_data))
        return mse

# Debugging usage example
if __name__ == "__main__":
    plugin = Plugin()
    plugin.configure_size(interface_size=4, output_shape=128)
    debug_info = plugin.get_debug_info()
    print(f"Debug Info: {debug_info}")
