import numpy as np
from keras.models import Model, load_model
from keras.callbacks import EarlyStopping, ModelCheckpoint
import tensorflow as tf
from keras.optimizers import Adam
from tensorflow.keras.losses import Huber
from tensorflow.keras.mixed_precision import set_global_policy

set_global_policy('mixed_float16')

class AutoencoderManager:
    def __init__(self, encoder_plugin, decoder_plugin):
        self.encoder_plugin = encoder_plugin
        self.decoder_plugin = decoder_plugin
        self.autoencoder_model = None
        self.encoder_model = None
        self.decoder_model = None
        print(f"[AutoencoderManager] Initialized with encoder plugin and decoder plugin")

    def build_autoencoder(self, input_shape, interface_size, config, num_channels):
        try:
            print("[build_autoencoder] Starting to build autoencoder...")

            # Determine if sliding windows are used
            use_sliding_windows = config.get('use_sliding_windows', True)

            # Configure encoder size
            self.encoder_plugin.configure_size(input_shape, interface_size, num_channels, use_sliding_windows)

            # Get the encoder model
            self.encoder_model = self.encoder_plugin.encoder_model
            print("[build_autoencoder] Encoder model built and compiled successfully")
            self.encoder_model.summary()

            # Get the encoder's output shape
            encoder_output_shape = self.encoder_model.output_shape[1:]  # Exclude batch size
            print(f"Encoder output shape: {encoder_output_shape}")

            # Configure the decoder size, passing the encoder's output shape
            self.decoder_plugin.configure_size(interface_size, input_shape, num_channels, encoder_output_shape, use_sliding_windows)

            # Get the decoder model
            self.decoder_model = self.decoder_plugin.model
            print("[build_autoencoder] Decoder model built and compiled successfully")
            self.decoder_model.summary()

            # Build autoencoder model
            autoencoder_output = self.decoder_model(self.encoder_model.output)
            self.autoencoder_model = Model(inputs=self.encoder_model.input, outputs=autoencoder_output, name="autoencoder")

            # Define optimizer
            adam_optimizer = Adam(
                learning_rate=config['learning_rate'],  # Set the learning rate
                beta_1=0.9,  # Default value
                beta_2=0.999,  # Default value
                epsilon=1e-7,  # Default value
                amsgrad=False,  # Default value
                clipnorm=1.0,  # Gradient clipping
                clipvalue=0.5  # Gradient clipping
            )

            # Define custom R² score metric
            def r2_score(y_true, y_pred):
                """Calculate R² score."""
                ss_res = tf.reduce_sum(tf.square(y_true - y_pred))  # Residual sum of squares
                ss_tot = tf.reduce_sum(tf.square(y_true - tf.reduce_mean(y_true)))  # Total sum of squares
                return 1 - (ss_res / (ss_tot + tf.keras.backend.epsilon()))  # Avoid division by zero

            # Compile autoencoder with the custom loss function
            self.autoencoder_model.compile(
                optimizer=adam_optimizer,
                loss=Huber(delta=1.0),
                metrics=['mae'],
                run_eagerly=True
            )
            print("[build_autoencoder] Autoencoder model built and compiled successfully")
            self.autoencoder_model.summary()
        except Exception as e:
            print(f"[build_autoencoder] Exception occurred: {e}")
            raise






    def train_autoencoder(self, data, epochs=100, batch_size=32, config=None):
        try:
            print(f"[train_autoencoder] Received data with shape: {data.shape}")

            # Determine if sliding windows are used
            use_sliding_windows = config.get('use_sliding_windows', True)

            # Check and reshape data for compatibility with Conv1D layers
            if not use_sliding_windows and len(data.shape) == 2:  # Row-by-row data (2D)
                print("[train_autoencoder] Reshaping data to add channel dimension for Conv1D compatibility...")
                data = np.expand_dims(data, axis=-1)  # Add channel dimension (num_samples, num_features, 1)
                print(f"[train_autoencoder] Reshaped data shape: {data.shape}")

            num_channels = data.shape[-1]
            input_shape = data.shape[1]
            interface_size = self.encoder_plugin.params.get('interface_size', 4)

            # Build autoencoder with the correct num_channels
            if not self.autoencoder_model:
                self.build_autoencoder(input_shape, interface_size, config, num_channels)

            # Validate data for NaN values before training
            if np.isnan(data).any():
                raise ValueError("[train_autoencoder] Training data contains NaN values. Please check your data preprocessing pipeline.")

            # Calculate entropy and useful information using Shannon-Hartley theorem
            self.calculate_dataset_information(data, config)

            print(f"[train_autoencoder] Training autoencoder with data shape: {data.shape}")

            # Implement Early Stopping
            early_stopping = EarlyStopping(monitor='loss', patience=3, restore_best_weights=True)

            # Start training with early stopping
            history = self.autoencoder_model.fit(
                data,
                data,
                epochs=epochs,
                batch_size=batch_size,
                verbose=1,
                callbacks=[early_stopping]
            )

            # Log training loss
            print(f"[train_autoencoder] Training loss values: {history.history['loss']}")
            print("[train_autoencoder] Training completed.")
        except Exception as e:
            print(f"[train_autoencoder] Exception occurred during training: {e}")
            raise



    def calculate_dataset_information(self, data, config):
        try:
            print("[calculate_dataset_information] Calculating dataset entropy and useful information...")

            # Handle 2D and 3D data shapes
            normalized_columns = []
            if len(data.shape) == 3:  # Sliding window data
                for col in range(data.shape[-1]):
                    column_data = data[:, :, col].flatten()  # Flatten the column data
                    min_val, max_val = column_data.min(), column_data.max()
                    normalized_column = (column_data - min_val) / (max_val - min_val)  # Min-max normalization
                    normalized_columns.append(normalized_column)
            elif len(data.shape) == 2:  # Row-by-row data
                for col in range(data.shape[1]):
                    column_data = data[:, col]  # No need to flatten, already 1D
                    min_val, max_val = column_data.min(), column_data.max()
                    normalized_column = (column_data - min_val) / (max_val - min_val)  # Min-max normalization
                    normalized_columns.append(normalized_column)
            else:
                raise ValueError("[calculate_dataset_information] Unsupported data shape for processing.")

            concatenated_data = np.concatenate(normalized_columns, axis=0)
            num_samples = concatenated_data.shape[0]  # Correct number of samples is the length of concatenated vector

            # Convert concatenated data to TensorFlow tensor for acceleration
            concatenated_data_tf = tf.convert_to_tensor(concatenated_data, dtype=tf.float32)

            # Calculate signal-to-noise ratio (SNR) using TensorFlow
            mean_val = tf.reduce_mean(concatenated_data_tf)
            std_val = tf.math.reduce_std(concatenated_data_tf)
            snr = tf.cond(
                tf.greater(std_val, 0),
                lambda: (mean_val / std_val) ** 2,
                lambda: tf.constant(0.0, dtype=tf.float32)
            )

            # Retrieve dataset periodicity and calculate sampling frequency
            periodicity = config['dataset_periodicity']
            periodicity_seconds_map = {
                "1min": 60,
                "5min": 5 * 60,
                "15min": 15 * 60,
                "1h": 60 * 60,
                "4h": 4 * 60 * 60,
                "daily": 24 * 60 * 60
            }
            sampling_period_seconds = periodicity_seconds_map.get(periodicity, None)

            if sampling_period_seconds:
                sampling_frequency = tf.constant(1 / sampling_period_seconds, dtype=tf.float32)
            else:
                sampling_frequency = tf.constant(0.0, dtype=tf.float32)

            # Calculate Shannon-Hartley channel capacity and total useful information
            channel_capacity = tf.cond(
                tf.math.logical_and(tf.greater(snr, 0), tf.greater(sampling_frequency, 0)),
                lambda: sampling_frequency * tf.math.log(1 + snr) / tf.math.log(2.0),
                lambda: tf.constant(0.0, dtype=tf.float32)
            )
            total_information_bits = channel_capacity * num_samples * sampling_period_seconds

            # Calculate entropy using TensorFlow histogram binning
            bins = 1000  # Increased bin count for better precision
            histogram = tf.histogram_fixed_width(concatenated_data_tf, [0.0, 1.0], nbins=bins)
            histogram = tf.cast(histogram, tf.float32)
            probabilities = histogram / tf.reduce_sum(histogram)
            entropy = -tf.reduce_sum(probabilities * tf.math.log(probabilities + 1e-10) / tf.math.log(2.0))  # Avoid log(0)

            # Log calculated information
            print(f"[calculate_dataset_information] Calculated SNR: {snr.numpy()}")
            print(f"[calculate_dataset_information] Sampling frequency: {sampling_frequency.numpy()} Hz")
            print(f"[calculate_dataset_information] Channel capacity: {channel_capacity.numpy()} bits/second")
            print(f"[calculate_dataset_information] Total useful information: {total_information_bits.numpy()} bits")
            print(f"[calculate_dataset_information] Entropy: {entropy.numpy()} bits")
        except Exception as e:
            print(f"[calculate_dataset_information] Exception occurred: {e}")
            raise



    def evaluate(self, data, dataset_name, config):
        """
        Evaluate the autoencoder model on the provided dataset and calculate the MSE and MAE.

        Args:
            data (np.ndarray): Input data to evaluate (original input data).
            dataset_name (str): Name of the dataset (e.g., "Training" or "Validation").
            config (dict): Configuration dictionary.

        Returns:
            tuple: Calculated MSE and MAE for the dataset.
        """
        print(f"[evaluate] Evaluating {dataset_name} data with shape: {data.shape}")

        # Reshape data for Conv1D compatibility if sliding windows are not used
        if not config.get('use_sliding_windows', True) and len(data.shape) == 2:
            data = np.expand_dims(data, axis=-1)
            print(f"[evaluate] Reshaped {dataset_name} data for Conv1D compatibility: {data.shape}")

        # Evaluate the autoencoder
        results = self.autoencoder_model.evaluate(data, data, verbose=1)
        mse, mae = results[0], results[1]  # Retrieve MSE (loss) and MAE

        print(f"[evaluate] {dataset_name} Evaluation results - MSE: {mse}, MAE: {mae}")
        return mse, mae






    def encode_data(self, data, config):
        print(f"[encode_data] Encoding data with shape: {data.shape}")

        # Determine if sliding windows are used
        use_sliding_windows = config.get('use_sliding_windows', True)

        # Reshape data for sliding windows or row-by-row processing
        if use_sliding_windows:
            if config['window_size'] > data.shape[1]:
                raise ValueError("[encode_data] window_size cannot be greater than the number of features in the data.")
            num_channels = data.shape[1] // config['window_size']
            if num_channels <= 0:
                raise ValueError("[encode_data] Invalid num_channels calculated for sliding window data.")
            if data.shape[1] % config['window_size'] != 0:
                raise ValueError("[encode_data] data.shape[1] must be divisible by window_size for sliding windows.")
            data = data.reshape((data.shape[0], config['window_size'], num_channels))
        else:
            # For row-by-row data, add a channel dimension
            num_channels = 1
            data = np.expand_dims(data, axis=-1)

        print(f"[encode_data] Reshaped data shape for encoding: {data.shape}")

        # Perform encoding
        try:
            encoded_data = self.encoder_model.predict(data)
            print(f"[encode_data] Encoded data shape: {encoded_data.shape}")
            return encoded_data
        except Exception as e:
            print(f"[encode_data] Exception occurred during encoding: {e}")
            raise ValueError("[encode_data] Failed to encode data. Please check model compatibility and data shape.")




   
    def decode_data(self, encoded_data, config):
        print(f"[decode_data] Decoding data with shape: {encoded_data.shape}")
        decoded_data = self.decoder_model.predict(encoded_data)

        if not config['use_sliding_windows']:
            # Reshape decoded data for row-by-row processing
            decoded_data = decoded_data.reshape((decoded_data.shape[0], config['original_feature_size']))
            print(f"[decode_data] Reshaped decoded data to match original feature size: {decoded_data.shape}")
        else:
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

    def calculate_mse(self, original_data, reconstructed_data, config):
        print(f"[calculate_mse] Original data shape: {original_data.shape}")
        print(f"[calculate_mse] Reconstructed data shape: {reconstructed_data.shape}")

        use_sliding_windows = config.get('use_sliding_windows', True)

        # Handle sliding windows: Aggregate reconstructed data if necessary
        if use_sliding_windows:
            window_size = config['window_size']
            num_channels = original_data.shape[1] // window_size

            # Reshape reconstructed data to match original sliding window format
            if reconstructed_data.shape != original_data.shape:
                print("[calculate_mse] Adjusting reconstructed data shape for sliding window comparison...")
                reconstructed_data = reconstructed_data.reshape(
                    (original_data.shape[0], original_data.shape[1])
                )

        # Ensure the data shapes match after adjustments
        if original_data.shape != reconstructed_data.shape:
            raise ValueError(f"Shape mismatch: original data shape {original_data.shape} does not match reconstructed data shape {reconstructed_data.shape}")

        # Calculate MSE
        mse = np.mean(np.square(original_data - reconstructed_data))
        print(f"[calculate_mse] Calculated MSE: {mse}")
        return mse


    def calculate_mae(self, original_data, reconstructed_data, config):
        """
        Calculate the Mean Absolute Error (MAE) between original and reconstructed data.
        """
        print(f"[calculate_mae] Original data shape: {original_data.shape}")
        print(f"[calculate_mae] Reconstructed data shape: {reconstructed_data.shape}")

        # Ensure the data shapes match
        if original_data.shape != reconstructed_data.shape:
            raise ValueError(f"Shape mismatch: original data shape {original_data.shape} does not match reconstructed data shape {reconstructed_data.shape}")

        # Calculate MAE consistently
        mae = tf.reduce_mean(tf.abs(original_data - reconstructed_data)).numpy()
        print(f"[calculate_mae] Calculated MAE: {mae}")
        return mae


    def calculate_mse(self, original_data, reconstructed_data, config):
        """
        Calculate the Mean Squared Error (MSE) between original and reconstructed data.
        """
        print(f"[calculate_mse] Original data shape: {original_data.shape}")
        print(f"[calculate_mse] Reconstructed data shape: {reconstructed_data.shape}")

        # Ensure the data shapes match
        if original_data.shape != reconstructed_data.shape:
            raise ValueError(f"Shape mismatch: original data shape {original_data.shape} does not match reconstructed data shape {reconstructed_data.shape}")

        # Calculate MSE consistently
        mse = tf.reduce_mean(tf.square(original_data - reconstructed_data)).numpy()
        print(f"[calculate_mse] Calculated MSE: {mse}")
        return mse





