import json
import requests
from app.config import DEFAULT_VALUES

def load_config(file_path):
    print(f"Loading configuration from file: {file_path}")
    with open(file_path, 'r') as f:
        config = json.load(f)
    print(f"Loaded configuration: {config}")
    return config

def save_config(config, path='config_out.json'):
    config_to_save = {k: v for k, v in config.items() if k not in DEFAULT_VALUES or v != DEFAULT_VALUES[k]}
    print(f"Saving configuration to file: {path}")
    print(f"Configuration to save: {config_to_save}")
    with open(path, 'w') as f:
        json.dump(config_to_save, f, indent=4)
    return config, path

def merge_config(file_config, cli_args, unknown_args, encoder_plugin, decoder_plugin):
    print(f"Pre-Merge: default config: {DEFAULT_VALUES}")

    # Start with the defaults
    merged_config = DEFAULT_VALUES.copy()
    print(f"Initial merged config with defaults: {merged_config}")
    print(f"Initial incremental_search: {merged_config.get('incremental_search')}")

    # Add plugin defaults
    encoder_plugin_params = encoder_plugin.plugin_params.copy()
    decoder_plugin_params = decoder_plugin.plugin_params.copy()
    merged_config.update(encoder_plugin_params)
    merged_config.update(decoder_plugin_params)
    print(f"After adding plugin defaults: {merged_config}")
    print(f"After adding plugin incremental_search: {merged_config.get('incremental_search')}")

    # Update with the file configuration if present
    if file_config:
        merged_config.update(file_config)
        print(f"After updating with file config: {merged_config}")
        print(f"After file config incremental_search: {merged_config.get('incremental_search')}")

    # Filter out CLI arguments that are None
    cli_args_filtered = {k: v for k, v in cli_args.items() if v is not None}
    print(f"CLI arguments to merge: {cli_args_filtered}")

    # Update with CLI arguments if they are provided
    merged_config.update(cli_args_filtered)
    print(f"After updating with CLI arguments: {merged_config}")
    print(f"After CLI args incremental_search: {merged_config.get('incremental_search')}")

    print(f"Pre-Merge: file config: {file_config}")
    print(f"Pre-Merge: cli_args: {cli_args_filtered}")

    print(f"Encoder plugin params before merging: {encoder_plugin_params}")
    print(f"Decoder plugin params before merging: {decoder_plugin_params}")

    for key, value in unknown_args.items():
        if key in encoder_plugin_params:
            encoder_plugin_params[key] = type(encoder_plugin_params[key])(value)
        if key in decoder_plugin_params:
            decoder_plugin_params[key] = type(decoder_plugin_params[key])(value)

    print(f"Encoder plugin params after merging: {encoder_plugin_params}")
    print(f"Decoder plugin params after merging: {decoder_plugin_params}")

    # Ensure the merged config reflects true values provided by the user or CLI args
    merged_config.update({k: v for k, v in encoder_plugin_params.items() if k not in DEFAULT_VALUES or v != DEFAULT_VALUES[k]})
    merged_config.update({k: v for k, v in decoder_plugin_params.items() if k not in DEFAULT_VALUES or v != DEFAULT_VALUES[k]})
    print(f"After updating with plugin params: {merged_config}")
    print(f"After plugin params incremental_search: {merged_config.get('incremental_search')}")

    print(f"Post-Merge: {merged_config}")
    return merged_config

def configure_with_args(config, args):
    config.update(args)
    return config

def save_debug_info(debug_info, encoder_plugin, decoder_plugin, path='debug_out.json'):
    encoder_debug_info = encoder_plugin.get_debug_info()
    decoder_debug_info = decoder_plugin.get_debug_info()

    debug_info = {
        'execution_time': debug_info.get('execution_time', 0),
        'encoder': encoder_debug_info,
        'decoder': decoder_debug_info
    }

    print(f"Saving debug information to file: {path}")
    with open(path, 'w') as f:
        json.dump(debug_info, f, indent=4)
    print(f"Debug information saved to {path}")

def load_remote_config(url, username, password):
    print(f"Loading remote configuration from URL: {url}")
    response = requests.get(url, auth=(username, password))
    response.raise_for_status()
    config = response.json()
    print(f"Loaded remote configuration: {config}")
    return config

def save_remote_config(config, url, username, password):
    print(f"Saving configuration to remote URL: {url}")
    response = requests.post(url, auth=(username, password), json=config)
    response.raise_for_status()
    success = response.status_code == 200
    print(f"Configuration saved to remote URL: {success}")
    return success

def log_remote_data(data, url, username, password):
    print(f"Logging data to remote URL: {url}")
    response = requests.post(url, auth=(username, password), json=data)
    response.raise_for_status()
    success = response.status_code == 200
    print(f"Data logged to remote URL: {success}")
    return success
