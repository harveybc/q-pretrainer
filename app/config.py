DEFAULT_VALUES = {
    'input_file': './tests/data/y_training_close_EURUSD_1h_2005_2012.csv.csv',
    'validation_file': './tests/data/y_validation_close_EURUSD_1h_2012_2020.csv',
    'output_file': './csv_output.csv',
    'save_encoder': './encoder_model.h5',
    'save_decoder': './decoder_model.h5',
    'load_encoder': None,
    'load_decoder': None,
    'evaluate_encoder': './encoder_eval.csv',
    'evaluate_decoder': './decoder_eval.csv',
    'encoder_plugin': 'default',
    'decoder_plugin': 'default',
    'window_size': 128,
    'threshold_error': 0.01,
    'initial_size': 126,
    'step_size': 16,
    'save_log': './debug_out.json',
    'remote_log': None,
    'remote_load_config': None,
    'remote_save_config': None,
    'username': None,
    'password': None, 
    'load_config': None,
    'save_config': './config_out.json',
    'quiet_mode': False,
    'force_date': False,
    'incremental_search': True,
    'headers': False,
    'epochs': 100,  # Add epochs here
    'batch_size': 32,  # Add batch_size here
    'learning_rate': 0.001,  # Add learning_rate here
}

