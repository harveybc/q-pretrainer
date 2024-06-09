import sys
import requests
import numpy as np
from app.data_handler import load_csv, write_csv, sliding_window
from app.plugin_loader import load_encoder_decoder_plugins
from app.reconstruction import reconstruct_from_windows

def train_autoencoder(encoder, decoder, data, mse_threshold, initial_size, step_size, incremental_search, epochs):
    current_size = initial_size
    current_mse = float('inf')
    print(f"Training autoencoder with initial size {current_size}...")

    while current_size > 0 and ((current_mse > mse_threshold) if not incremental_search else (current_mse < mse_threshold)):
        input_dim = data.shape[1]  # Use the window size as input dimension
        encoder.configure_size(input_dim=input_dim, encoding_dim=current_size)
        decoder.configure_size(encoding_dim=current_size, output_dim=input_dim)

        # Debugging information
        print(f"Configured encoder with input_dim={input_dim}, encoding_dim={current_size}")
        print(f"Configured decoder with encoding_dim={current_size}, output_dim={input_dim}")

        encoder.train(data)
        encoded_data = encoder.encode(data)
        decoder.train(encoded_data, data)

        encoded_data = encoder.encode(data)
        decoded_data = decoder.decode(encoded_data)
        current_mse = encoder.calculate_mse(data, decoded_data)
        print(f"Current MSE: {current_mse} at interface size: {current_size}")

        if (incremental_search and current_mse >= mse_threshold) or (not incremental_search and current_mse <= mse_threshold):
            print("Desired MSE reached. Stopping training.")
            break

        if incremental_search:
            current_size += step_size
            if current_size >= input_dim:
                break
        else:
            current_size -= step_size

    return encoder, decoder

def process_data(config):
    data = load_csv(config['csv_file'], headers=config['headers'])
    print(f"Data loaded: {data.shape[0]} rows and {data.shape[1]} columns.")

    if config['force_date']:
        data.index = pd.to_datetime(data.index)

    print(f"Data types:\n {data.dtypes}")

    debug_info = {}

    encoder_name = config.get('encoder_plugin', 'default_encoder')
    decoder_name = config.get('decoder_plugin', 'default_decoder')
    Encoder, encoder_params, Decoder, decoder_params = load_encoder_decoder_plugins(encoder_name, decoder_name)

    for column in data.columns:
        print(f"Processing column: {column}")
        column_data = data[[column]].values.astype(np.float64)
        windowed_data = sliding_window(column_data, config['window_size'])
        print(f"Windowed data shape: {windowed_data.shape}")

        reshaped_windowed_data = windowed_data.reshape(windowed_data.shape[0], windowed_data.shape[1])
        print(f"Reshaped windowed data shape: {reshaped_windowed_data.shape}")

        trained_encoder, trained_decoder = train_autoencoder(
            Encoder(), Decoder(), reshaped_windowed_data, config['mse_threshold'],
            config['initial_encoding_dim'], config['encoding_step_size'],
            config['incremental_search'], config['epochs']
        )

        encoder_model_filename = f"{config['save_encoder_path']}_{column}.keras"
        decoder_model_filename = f"{config['save_decoder_path']}_{column}.keras"
        trained_encoder.save(encoder_model_filename)
        trained_decoder.save(decoder_model_filename)
        print(f"Saved encoder model to {encoder_model_filename}")
        print(f"Saved decoder model to {decoder_model_filename}")

        encoded_data = trained_encoder.encode(reshaped_windowed_data)
        decoded_data = trained_decoder.decode(encoded_data)

        mse = trained_encoder.calculate_mse(reshaped_windowed_data, decoded_data)
        print(f"Mean Squared Error for column {column}: {mse}")
        debug_info[f'mean_squared_error_{column}'] = mse

        # Reconstruct the data to its original shape
        reconstructed_data = reconstruct_from_windows(decoded_data, data.shape[0], config['window_size'])
        print(f"Reconstructed data shape: {reconstructed_data.shape}")

        # Debugging information
        print(f"First 5 rows of reconstructed data: {reconstructed_data[:5]}")
        print(f"First 5 rows of original data: {data[[column]].values[:5]}")

        output_filename = f"{config['csv_output_path']}_{column}.csv"
        write_csv(output_filename, reconstructed_data, include_date=config['force_date'], headers=config['headers'])
        print(f"Output written to {output_filename}")

        # Print the encoder and decoder dimensions
        print(f"Encoder Dimensions: {trained_encoder.model.input_shape} -> {trained_encoder.model.output_shape}")
        print(f"Decoder Dimensions: {trained_decoder.model.input_shape} -> {trained_decoder.model.output_shape}")

    return reconstructed_data, debug_info
