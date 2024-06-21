import numpy as np
from keras.models import Model, load_model
from keras.optimizers import Adam

class AutoencoderManager:
    def __init__(self, encoder_plugin, decoder_plugin):
        self.encoder_plugin = encoder_plugin
        self.decoder_plugin = decoder_plugin
        self.encoder_model = None
        self.decoder_model = None
        self.autoencoder_model = None

    def build_autoencoder(self):
        try:
            print("[build_autoencoder] Starting to build autoencoder...")

            self.encoder_model = self.encoder_plugin.encoder_model
            print("[build_autoencoder] Encoder model built successfully")
            print(f"[build_autoencoder] Encoder model summary: {self.encoder_model.summary()}")

            self.decoder_model = self.decoder_plugin.decoder_model
            print("[build_autoencoder] Decoder model built successfully")
            print(f"[build_autoencoder] Decoder model summary: {self.decoder_model.summary()}")

            # Autoencoder
            encoder_output = self.encoder_model(self.encoder_model.input)
            autoencoder_output = self.decoder_model(encoder_output)
            self.autoencoder_model = Model(inputs=self.encoder_model.input, outputs=autoencoder_output, name="autoencoder")
            self.autoencoder_model.compile(optimizer=Adam(), loss='mean_squared_error')
            print("[build_autoencoder] Autoencoder model built and compiled successfully")
            print(f"[build_autoencoder] Autoencoder model summary: {self.autoencoder_model.summary()}")

            # Validate models
            if not self.encoder_model or not self.decoder_model or not self.autoencoder_model:
                raise ValueError("[build_autoencoder] Failed to build encoder, decoder, or autoencoder model")
        except Exception as e:
            print(f"[build_autoencoder] Exception occurred: {e}")
            raise

    def train_autoencoder(self, data, epochs=10, batch_size=256):
        try:
            if isinstance(data, tuple):
                data = data[0]  # Ensure data is not a tuple
            print(f"[train_autoencoder] Training autoencoder with data shape: {data.shape}")
            self.autoencoder_model.fit(data, data, epochs=epochs, batch_size=batch_size, verbose=1)
            print("[train_autoencoder] Training completed.")
        except Exception as e:
            print(f"[train_autoencoder] Exception occurred during training: {e}")
            raise

    def encode_data(self, data):
        print(f"[encode_data] Encoding data with shape: {data.shape}")
        encoded_data = self.encoder_model.predict(data)
        print(f"[encode_data] Encoded data shape: {encoded_data.shape}")
        return encoded_data

    def decode_data(self, encoded_data):
        print(f"[decode_data] Decoding data with shape: {encoded_data.shape}")
        decoded_data = self.decoder_model.predict(encoded_data)
        print(f"[decode_data] Decoded data shape: {decoded_data.shape}")
        return decoded_data

    def save_encoder(self, file_path):
        self.encoder_model.save(file_path)
        print(f"[save_encoder] Encoder model saved to {file_path}")

    def save_decoder(self, file_path):
        self.decoder_model.save(file_path)
        print(f"[save_decoder] Decoder model saved to {file_path}")

    def load_encoder(self, file_path):
        self.encoder_model = load_model(file_path)
        print(f"[load_encoder] Encoder model loaded from {file_path}")

    def load_decoder(self, file_path):
        self.decoder_model = load_model(file_path)
        print(f"[load_decoder] Decoder model loaded from {file_path}")

    def calculate_mse(self, original_data, reconstructed_data):
        original_data = original_data.reshape((original_data.shape[0], -1))  # Flatten the data
        reconstructed_data = reconstructed_data.reshape((original_data.shape[0], -1))  # Flatten the data
        mse = np.mean(np.square(original_data - reconstructed_data))
        print(f"[calculate_mse] Calculated MSE: {mse}")
        return mse
