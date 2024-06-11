import sys
import json
from app.config_handler import load_config, save_config, merge_config, save_debug_info
from app.cli import parse_args
from app.data_processor import process_data
from app.config import DEFAULT_VALUES

def main():
    print("Parsing initial arguments...")
    args, unknown_args = parse_args()
    print(f"Initial args: {args}")
    print(f"Unknown args: {unknown_args}")

    print("Loading configuration...")
    config = DEFAULT_VALUES.copy()

    if args.load_config:
        file_config = load_config(args.load_config)
        print(f"Loaded config from file: {file_config}")
        config.update(file_config)

    print("Merging configuration with CLI arguments and unknown args...")
    config = merge_config(config, vars(args), unknown_args)
    print(f"Config after merging: {config}")

    if args.save_config:
        print(f"Saving configuration to {args.save_config}...")
        save_config(config, args.save_config)
        print(f"Configuration saved to {args.save_config}.")

    print("Processing data...")
    decoded_data, debug_info = process_data(config)

    if not args.quiet_mode:
        print("Processed data:")
        print(decoded_data)
        print("Debug information:")
        print(json.dumps(debug_info, indent=4))

if __name__ == "__main__":
    main()
