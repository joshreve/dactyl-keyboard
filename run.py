import os.path as path
import getopt, sys
import src.argument_parser as parser

args = parser.parse()

if len(args['args']) < 1:
    print("A command must be specified")
    sys.exit(1)

command = args['args'][0]
if command not in ('help', 'generate', 'configure', 'realease'):
    print("Invalid command. Try 'help'")
    sys.exit(1)

def show_usage():
    print("Dactyl-Manuform Keyboard Generator")
    print("")
    print("Use this tool to configure and generate files for building a keyboard.")
    print("")
    print("")
    print("Usage:")
    print("  run.py [-d|--debug] [-u|--update] [--config <configuration-name>] <command>")
    print("")
    print("Available Commands:")
    print("  help        Show this help")
    print("  release     Run model_builder.py")
    print("  generate    Output the keyboard files to the './things' directory")
    print("  configure   Generate a configuration file with default values. The config")
    print("              file will be saved to configs/<configuration-name>. If the")
    print("              --config flag is not set, the default config_name will be used.")
    print("")
    print("Flags:")
    print("  --config     Set the configuration file to use, relative to the './configs'")
    print("               directory.")
    print("  -u|--update  Update a config file. This flag must be set if the config file")
    print("               already exists.")
    print("  -d|--debug   Show debug output")
    print("")

if command == 'help':
    show_usage()
elif command == 'generate':
    import src.dactyl_manuform as command
    command.run(args)
elif command == 'configure':
    import src.generate_configuration as command
    command.save_config(args)
elif command == 'release':
    import src.model_builder as command
    command.run()


