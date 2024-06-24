# Configuration file for the feature-extractor application

# Default configuration values
DEFAULT_VALUES = {
    'csv_file': './csv_input.csv',                   
    'save_encoder': './encoder_model.h5',            
    'save_decoder': './decoder_model.h5',            
    'load_encoder': None,                            
    'load_decoder': None,                            
    'evaluate_encoder': './encoder_eval.csv',        
    'evaluate_decoder': './decoder_eval.csv',        
    'encoder_plugin': 'default',                     
    'decoder_plugin': 'default',                     
    'window_size': 512,                              
    'threshold_error': 0.005,                        
    'initial_size': 8,                               
    'step_size': 4,                                  
    'remote_log': None,                              
    'remote_config': None,                           
    'load_config': './config_in.json',               
    'save_config': './config_out.json',              
    'quiet_mode': False,                             
    'force_date': False,                             
    'incremental_search': True,
    'headers': False                                 # Default setting for CSV headers
}
