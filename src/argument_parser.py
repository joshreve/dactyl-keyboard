import os.path as path
import getopt, sys

def parse():
    # set defaults
    debug = False
    update = False
    config_name = 'DM'
    relative_path = r".";
    file_name = "run_config"
    format = 'json'
    absolute_path = path.abspath(path.join(__file__, r"..", relative_path, file_name + r"." + format))

    opts, args = getopt.getopt(sys.argv[1:], "ud", ["config=", "update", "debug"])
    for opt, arg in opts:
        if opt in ('--config'):
            config_path_parts = arg.split(r'/')
            file_parts = config_path_parts.pop().split(r'.')

            file_name = file_parts[0]
            if len(file_parts) == 2:
                format = file_parts[1]
            
            config_name = file_name

            if len(config_path_parts) > 0:
                relative_path = path.join(*config_path_parts)

            absolute_path = path.abspath(path.join(__file__, r"..", r"..", "configs", relative_path, file_name + r"." + format))
        elif opt in ('-u', "--update"):
            update = True
        elif opt in ('-d', "--debug"):
            debug = True


    if debug:
        print("CONFIG OPTIONS")
        print("config.name:          " + config_name)
        print("config.relative_path: " + relative_path)
        print("config.file_name:     " + file_name)
        print("config.format:        " + format)
        print("config.absolute_path: " + absolute_path)
        print("update:               " + str(update))
        print("opts:                 " + str(opts))
        print("args:                 " + str(args))
        print("")
        
    return {
        'config': {
            'name': config_name,
            'relative_path': relative_path,
            'file_name': file_name,
            'format': format,
            'absolute_path': absolute_path
        },
        'debug': debug,
        'update': update,
        'opts': opts,
        'args': args
    }