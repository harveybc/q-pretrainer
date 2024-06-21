import pandas as pd
from app.autoencoder_manager import AutoencoderManager
from app.data_handler import write_csv
from app.reconstruction import unwindow_data

def process_data(config):
    """
    Process the data as per the given configuration.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        processed_data (dict): Processed data.
        debug_info (dict): Debug information.
    """
    # Your existing data processing logic
    processed_data = {}  # Placeholder for processed data
    debug_info = {}  # Placeholder for debug information
    # Add your data processing logic here
    print(f"Processed data: {processed_data}")
    print(f"Debug info: {debug_info}")

    return processed_data, debug_info

def run_autoencoder_pipeline(config, encoder_plugin, decoder_plugin):
    """
    Run the autoencoder training and evaluation pipeline.

    Args:
        config (dict): The configuration dictionary.
        encoder_plugin (object): Encoder plugin instance.
        decoder_plugin (object): Decoder plugin instance.

    Returns:
        None
    """
    print("Running process_data...")
    processed_data, debug_info = process_data(config)
    print("Processed data received.")

    for column, windowed_data in processed_data.items():
        print(f"Processing column: {column}")
        autoencoder_manager = AutoencoderManager(encoder_plugin, decoder_plugin)
        autoencoder_manager.build_autoencoder()
        autoencoder_manager.train_autoencoder(windowed_data, epochs=config['epochs'], batch_size=config['training_batch_size'])

        encoder_model_filename = f"{config['save_encoder_path']}_{column}.keras"
        decoder_model_filename = f"{config['save_decoder_path']}_{column}.keras"
        autoencoder_manager.save_encoder(encoder_model_filename)
        autoencoder_manager.save_decoder(decoder_model_filename)
        print(f"Saved encoder model to {encoder_model_filename}")
        print(f"Saved decoder model to {decoder_model_filename}")

        encoded_data = autoencoder_manager.encode_data(windowed_data)
        decoded_data = autoencoder_manager.decode_data(encoded_data)

        mse = autoencoder_manager.calculate_mse(windowed_data, decoded_data)
        print(f"Mean Squared Error for column {column}: {mse}")

        # Perform unwindowing of the decoded data
        reconstructed_data = unwindow_data(pd.DataFrame(decoded_data.reshape(decoded_data.shape[0], decoded_data.shape[1])))
        
        output_filename = f"{config['csv_output_path']}_{column}.csv"
        write_csv(output_filename, reconstructed_data, include_date=config['force_date'], headers=config['headers'], window_size=config['window_size'])
        print(f"Output written to {output_filename}")

        print(f"Encoder Dimensions: {autoencoder_manager.encoder_model.input_shape} -> {autoencoder_manager.encoder_model.output_shape}")
        print(f"Decoder Dimensions: {autoencoder_manager.decoder_model.input_shape} -> {autoencoder_manager.decoder_model.output_shape}")
