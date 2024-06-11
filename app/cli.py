import argparse

def parse_args():
    """
    Parse command-line arguments for the feature-extractor application.

    Returns:
        tuple: Parsed known arguments and unknown arguments.
    """
    parser = argparse.ArgumentParser(description="Feature-extractor: A tool for encoding and decoding CSV data with support for dynamic plugins.")
    parser.add_argument('csv_file', type=str, help='Path to the CSV file to process.')
    parser.add_argument('-se', '--save_encoder', type=str, help='Filename to save the trained encoder model.', default='./encoder_ann.keras')
    parser.add_argument('-sd', '--save_decoder', type=str, help='Filename to save the trained decoder model.', default='./decoder_ann.keras')
    parser.add_argument('-le', '--load_encoder', type=str, help='Filename to load encoder parameters from.')
    parser.add_argument('-ld', '--load_decoder', type=str, help='Filename to load decoder parameters from.')
    parser.add_argument('-ee', '--evaluate_encoder', type=str, help='Filename for outputting encoder evaluation results.')
    parser.add_argument('-ed', '--evaluate_decoder', type=str, help='Filename for outputting decoder evaluation results.')
    parser.add_argument('-ep', '--encoder_plugin', type=str, default='default', help='Name of the encoder plugin to use.')
    parser.add_argument('-dp', '--decoder_plugin', type=str, default='default', help='Name of the decoder plugin to use.')
    parser.add_argument('-ws', '--window_size', type=int, help='Sliding window size to use for processing time series data.')
    parser.add_argument('-me', '--max_error', type=float, help='Maximum MSE threshold to stop the training process.', default=0.3)
    parser.add_argument('-is', '--initial_size', type=int, help='Initial size of the encoder/decoder interface.', default=256)
    parser.add_argument('-ss', '--step_size', type=int, help='Step size to adjust the size of the encoder/decoder interface.', default=32)
    parser.add_argument('-rl', '--remote_log', type=str, help='URL of a remote data-logger API endpoint.')
    parser.add_argument('-rc', '--remote_config', type=str, help='URL of a remote JSON configuration file to download and execute.')
    parser.add_argument('-lc', '--load_config', type=str, help='Path to load a configuration file.')
    parser.add_argument('-sc', '--save_config', type=str, help='Path to save the current configuration.')
    parser.add_argument('-qm', '--quiet_mode', action='store_true', help='Suppress output messages.')
    parser.add_argument('-fd', '--force_date', action='store_true', help='Include date in the output CSV files.')
    parser.add_argument('-inc', '--incremental_search', action='store_true', help='Enable incremental search for interface size.')
    return parser.parse_known_args()
