#!/bin/bash

#                   *******************                   #
# *******************      setup      ******************* #
#                   *******************                   #

# exit if any errors are thrown
set -e

container=""
# bad practice:
    # container variable names MUST match
    # the positional name {positional}Container
shellContainer=DM-shell
runContainer=DM-run
autoloaderContainer=DM-autoloader
configContainer=DM-config
releaseBuildContainer=DM-release-build
containers=("$shellContainer" "$configContainer" "$runContainer" "$autoloaderContainer" "$releaseBuildContainer")

imageName=dactyl-keyboard
srcBind="$(pwd)/src:/app/src"
thingsBind="$(pwd)/things:/app/things"

# force exit on interrupt in case we are in a menu
function catch_interrupt() { exit 1; }
trap catch_interrupt SIGINT
trap catch_interrupt SIGTSTP

#                   *******************                   #
# *******************    functions    ******************* #
#                   *******************                   #

################################
# General Helpers
################################

function inform() {
  echo -e "\n[INFO] $@\n"
}

function warn() {
  echo -e "\n[WARN] $@\n"
}

function error() {
  echo -e "\n[ERROR] $@\n"
}

function exitUnexpectedPositionalArgs() {
  error "Unexpected positionnal argument.\n\n\tAlready had: $positional\n\n\tAnd then got: $1"
  exit 1
}

function exitUnexpectedFlags() {
  error "One or more flags are invalid:\n\n\tPositional: $positional\n\n\tFlags: $flags"
  exit 1
}

################################
# Interactive Menu
################################

# https://unix.stackexchange.com/questions/146570/arrow-key-enter-menu
#  Arguments:
#    array of options
#
#  Return value:
#    selected index (0 for opt1, 1 for opt2 ...)

function menu {
  local header="\n[Dactyl Manuform]"
  if [ $container ]; then
    header+=" -- $container"
  fi
  header+="\n\nPlease choose an option:\n\n"
  printf "$header"
	options=("$@")

	# helpers for terminal print control and key input
	ESC=$(printf "\033")
	cursor_blink_on()	{ printf "$ESC[?25h"; }
	cursor_blink_off()	{ printf "$ESC[?25l"; }
	cursor_to()			{ printf "$ESC[$1;${2:-1}H"; }
	print_option()		{ printf "\t   $1 "; }
	print_selected()	{ printf "\t${COLOR_GREEN}  $ESC[7m $1 $ESC[27m${NC}"; }
	get_cursor_row()	{ IFS=';' read -sdR -p $'\E[6n' ROW COL; echo ${ROW#*[}; }
  key_input() {
    local key
    # read 3 characters, 1 at a time
    for (( i=0; i < 3; ++i)); do
      read -s -n1 input 2>/dev/null >&2
      # concatenate chars together
      key+="$input"
      # if a number is encountered, echo it back
      if [[ $input =~ ^[1-9]$ ]]; then
        echo $input; return;
      # if enter, early return
      elif [[ $input = "" ]]; then
        echo enter; return;
      # if we encounter something other than [1-9] or "" or the escape sequence
      # then consider it an invalid input and exit without echoing back
      elif [[ ! $input = $ESC && i -eq 0 ]]; then
        return
      fi
    done

    if [[ $key = $ESC[A ]]; then echo up; fi;
    if [[ $key = $ESC[B ]]; then echo down; fi;
  }
  function cursorUp() { printf "$ESC[A"; }
  function clearRow() { printf "$ESC[2K\r"; }
  function eraseMenu() {
    cursor_to $lastrow
    clearRow
    numHeaderRows=$(printf "$header" | wc -l)
    numOptions=${#options[@]}
    numRows=$(($numHeaderRows + $numOptions))
    for ((i=0; i<$numRows; ++i)); do
      cursorUp; clearRow;
    done
  }

	# initially print empty new lines (scroll down if at bottom of screen)
	for opt in "${options[@]}"; do printf "\n"; done

	# determine current screen position for overwriting the options
	local lastrow=`get_cursor_row`
	local startrow=$(($lastrow - $#))
  local selected=0

	# ensure cursor and input echoing back on upon a ctrl+c during read -s
	trap "cursor_blink_on; stty echo; printf '\n'; exit" 2
	cursor_blink_off

	while true; do
    # print options by overwriting the last lines
		local idx=0
    for opt in "${options[@]}"; do
      cursor_to $(($startrow + $idx))
      # add an index to the option
      local label="$(($idx + 1)). $opt"
      if [ $idx -eq $selected ]; then
        print_selected "$label"
      else
        print_option "$label"
      fi
      ((idx++))
    done

		# user key control
    input=$(key_input)

		case $input in
			enter) break;;
      [1-9])
        # If a digit is encountered, consider it a selection (if within range)
        if [ $input -lt $(($# + 1)) ]; then
          selected=$(($input - 1))
          break
        fi
        ;;
			up)	((selected--));
					if [ $selected -lt 0 ]; then selected=$(($# - 1)); fi;;
			down)  ((selected++));
					if [ $selected -ge $# ]; then selected=0; fi;;
		esac
	done

  eraseMenu
	cursor_blink_on

	return $selected
}


################################
# Setup helpers
################################

function showHelpAndExit() {
cat << _end_of_text
[Dactyl Manuform]

A bash CLI to manage Docker artifacts for the Dactyl Keyboard project.

Run the script without any flags to use the interactive menu.

Usage:
  ./dactyl.sh 
  ./dactyl.sh [-h | --help | --uninstall]
  ./dactyl.sh image [--build | --inspect | --remove]
  ./dactyl.sh (config|run|autoloader|releaseBuild) [--build | --inspect | --start | --stop | --remove]
  ./dactyl.sh shell [--build | --inspect | --session | --start | --stop | --remove]
  ./dactyl.sh autoloader

Options:
  positional    Target the image or a particular container (shell | config | run | releaseBuild)
  -h --help     Show this screen.
  --uninstall   Remove all Docker artifacts.
  --build       Build (or rebuild) and run the target container.
  --inspect     Show "docker inspect" results for the target container.
  --start       Start or restart the target container.
  --stop        Stop the target container.
  --remove      Remove the target container.
  --session     Start a shell session in the shell container.
  --autoloader  Start autoloader script
_end_of_text
exit
}

# error on any unexpected flags or more than one positional argument
function processArgs() {
  while [[ $# -gt 0 ]]
    do
      key="$1"

      case $key in
        --autoloader)
        handleStartStopAutoloader
        exit 1
        ;;
        --build|--remove|--inspect|--session|--start|--stop)
          if [[ $flags ]]; then
            flags+=" $key"
          else
            flags=$key
          fi
          shift;;
        -h|--help) showHelpAndExit;;
        --uninstall) handleUninstall;;
        *)
          # all valid flags should have already been captured above
          if [[ $key == -* ]]; then
            error "Unknwon flag: $key"
            exit 1
          # if we already have a positional argument we shouldn't get another
          elif [[ "$positional" ]]; then
            exitUnexpectedPositionalArgs $key
            exit 1
          # the totality of accepted positional arguments
          elif [[ "$key" =~ ^(image|shell|config|run|releaseBuild|autoloader)$ ]]; then
            positional="$key"
            if [[ ! $key = image ]]; then
              key+="Container"
              container=$(echo "${!key}")
            fi
            shift
          else
            error "Unknown positional arg: \"$key\""
            exit 1
          fi
          ;;
      esac
    done
}

# installing docker is out of scope
# so if it isn't found, inform user and exit
function checkDocker() {
  if ! which docker &> /dev/null; then
    error "Docker is not installed.\n\n\tPlease visit https://www.docker.com/products/docker-desktop for more information."
    exit 1
  fi

  if ! docker image list &> /dev/null; then
    error "Docker is not running. Please start docker and try again."
    exit 1;
  fi
}

# exit unless user responds with yes
function confirmContinue() {
  while true; do
    read -p "$@ [y/n]" yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit 0;;
        * ) error "Please answer yes or no.";;
    esac
  done
}

################################
# Image Logic
################################

function imageExists() {
  docker image list | grep "$imageName" &> /dev/null
}

function buildImage() {
  inform "Building docker image: $imageName..."
  docker build -t dactyl-keyboard -f docker/Dockerfile .
}

function promptBuildImageIfNotExists() {
  if ! imageExists; then
    inform "Docker image not found: $imageName"
    confirmContinue "Would you like to build it now?"
    buildImage
  fi
}

# image will always exist if we are here
function handleRebuildImage() {
  warn "Docker image already exists: $imageName"
  confirmContinue "Would you like to overwrite it?"
  buildImage
}

function removeImage() {
  inform "Removing docker image: $imageName..."
  docker image rm $imageName
}

function handleRemoveImage() {
  warn "This will remove docker image: $imageName"
  confirmContinue "Would you like to continue?"
  removeImage
}

function handleInspectImage() {
  inform "Checking status of image: $imageName"
  docker image inspect $imageName
}

function handleImageMenu() {
  local check="Check Image Status"
  local build="Rebuild Image"
  local remove="Remove Image"
  local mainMenu="Main Menu"
  local end="Exit"
  options=("$check" "$build" "$remove" "$mainMenu" "$end")
  # execute in subshell so exit code doesn't exit the script
  (menu "${options[@]}") && true
  result="${options[$?]}"

  case $result in
    $check) handleInspectImage;;
    $build) handleRebuildImage;;
    $remove) handleRemoveImage;;
    $mainMenu) handleMainMenu;;
    *) exit;;
  esac
}

# if we made it this far, image is confirmed to exist
function handleImageCLI() {
  if [[ ! "$flags" ]]; then
    handleImageMenu
  elif [[ "$flags" =~ ^.*(--inspect).*$ ]]; then
    handleInspectImage
  elif [[ "$flags" =~ ^.*(--build).*$ ]]; then
    handleRebuildImage
  elif [[ "$flags" =~ ^.*(--remove).*$ ]]; then
    handleRemoveImage
  else
    exitUnexpectedFlags
  fi
}

################################
# Container Helpers
################################

function containerExists() {
  docker container list -a | grep "$container" &> /dev/null
}

function containerIsRunning() {
  if ! containerExists "$container"; then
    return 1
  fi
  docker container inspect $container | grep '"Status": "running",' &> /dev/null
}

function isShell() {
  test $container = $shellContainer
}

function promptIfShell() {
  if isShell; then
    promptStartShellSession
  fi
}

function buildContainerAndExecutePythonScript() {
  docker run --name $container -d -v "$srcBind" -v "$thingsBind" $imageName python3 -i $1
}

function buildContainer() {
  inform "Building docker container: $container..."
  case $container in
    $shellContainer)
      docker run --name $shellContainer -d -it -v "$srcBind" -v "$thingsBind" $imageName
      ;;
    $autoloaderContainer)
      buildContainerAndExecutePythonScript autoloader.py
      ;;
    $runContainer)
      buildContainerAndExecutePythonScript dactyl_manuform.py
      ;;
    $configContainer)
      buildContainerAndExecutePythonScript generate_configuration.py
      ;;
    $releaseBuildContainer)
      buildContainerAndExecutePythonScript model_builder.py
      ;;
    *)
      error "Unexpected exception. Containier: $container"
      exit 1;;
  esac
  echo
}

function buildContainerIfNotExists() {
  if ! containerExists; then
    warn "Container not found: $container"
    confirmContinue "Would you like to build it now?"
    buildContainer
  fi
}

function startContainer() {
  docker container start $container &> /dev/null
}

function promptStartContainerIfNotRunning() {
  buildContainerIfNotExists
  if ! containerIsRunning; then
    warn "Container is not running: $container"
    confirmContinue "Would you like to start it now?"
    startContainer
  fi
}

function startContainerIfNotRunning() {
  buildContainerIfNotExists
  if ! containerIsRunning; then
    inform "Starting docker container: $container"
    startContainer
  fi
}

function startContainerOrAlert() {
  if containerIsRunning; then
    inform "Container is already running: $shellContainer"
  else
    startContainerIfNotRunning
  fi

  if isShell; then
    promptStartShellSession
  fi
}

function stopContainer() {
  if containerIsRunning; then
    inform "Stopping docker container: $container..."
    docker container stop $container &> /dev/null
    docker container wait $container &> /dev/null
  fi
}

function handleStopContainer() {
  if ! containerExists; then
    warn "Docker container does not exist: $container"
  elif ! containerIsRunning; then
    inform "Container is already stopped: $container"
  else
    stopContainer
  fi
}

function removeContainer() {
  if containerExists; then
    stopContainer
    inform "Removing docker container: $container..."
    docker container rm $container &> /dev/null
  fi
}

function inspectContainer() {
  if ! containerExists; then
    inform "Container \"$container\" does not exist."
    confirmContinue "Would you like to build it?"
    buildContainer
  fi

  docker container inspect $container
}

function handleBuildContainer() {
  if containerExists; then
    warn "Container already exists: $container"
    confirmContinue "Would you like to overwrite it?"
    removeContainer
  fi

  buildContainer
  promptIfShell
}

function handleStartStopAutoloader() {
  container=$autoloaderContainer
  if ! containerExists; then
    buildContainer
    exit 1
  fi
  if ! containerIsRunning; then
    inform "Starting docker container: $container"
    startContainer
  else
    inform "Stopping docker container: $container"
    stopContainer
  fi
}

function handleContainerMenu() {
  local build="Rebuild $container Container"
  local start="Start $container Container"
  local stop="Stop $container Container"
  local remove="Remove $container Container"
  local inspect="Inspect $container Container"
  local session="Start $container Session"
  local main="Main Menu"
  local end="Exit"

  if ! containerExists; then
    build="Build and run $container Container"
    options=("$build" "$main" "$end")
  elif containerIsRunning && ! isShell; then
    options=("$inspect" "$build" "$stop" "$remove" "$main" "$end")
  elif containerIsRunning && isShell; then
    options=("$session" "$inspect" "$build" "$stop" "$remove" "$main" "$end")
  else
    options=("$inspect" "$build" "$start" "$remove" "$main" "$end")
  fi
  
  # execute in subshell so exit code doesn't exit the script
  (menu "${options[@]}") && true
  result="${options[$?]}"

  case $result in
    $build) handleBuildContainer;;
    $start) startContainerOrAlert;;
    $stop) handleStopContainer;;
    $remove) removeContainer;;
    $inspect) inspectContainer;;
    $main) handleMainMenu;;
    *) 
      if isShell && [[ $session = $result ]]; then
        startShellSession
      fi
      exit
      ;;
  esac
}

function handleContainerCLI() {
  if [[ ! "$flags" ]]; then
    handleContainerMenu
  elif [[ "$flags" =~ ^.*(--inspect).*$ ]]; then
    inspectContainer
  elif [[ "$flags" =~ ^.*(--build).*$ ]]; then
    handleBuildContainer
  elif [[ "$flags" =~ ^.*(--session).*$ ]] && isShell; then
    startShellSession
  elif [[ "$flags" =~ ^.*(--start).*$ ]]; then
    startContainerOrAlert
  elif [[ "$flags" =~ ^.*(--stop).*$ ]]; then
    handleStopContainer
  elif [[ "$flags" =~ ^.*(--remove).*$ ]]; then
    removeContainer
  else
    exitUnexpectedFlags
  fi
}

################################
# Shell Specific Logic
################################

function startShellSession() {
  promptStartContainerIfNotRunning
  inform "Starting session in container: $shellContainer\n\n\tType \"exit\" to terminate the session."
  docker exec -it $shellContainer /bin/bash
}

function promptStartShellSession() {
  confirmContinue "Would you like to start a shell session?"
  startShellSession
}

################################
# Uninstaller
################################

function handleUninstall() {
  warn "This will remove all containers and images."
  confirmContinue "Are you sure you want to continue?"
  for currentContainer in "${containers[@]}"; do
    container="$currentContainer"
    removeContainer
  done

  removeImage
  exit
}

################################
# Main Menu Logic
################################

function handleMainMenu() {
  container=""

  local imageOpt="Manage Docker Image"
  local shellOpt="$shellContainer Container"
  local autoloaderOpt="$autoloaderContainer Container"
  local configOpt="$configContainer Container"
  local releaseOpt="$releaseBuildContainer Container"
  local runOpt="$runContainer Container"
  local uninstallOpt="Uninstall"
  local help="Show Help"
  local end="Exit"

  options=("$imageOpt" "$shellOpt" "$autoloaderOpt" "$configOpt" "$runOpt" "$releaseOpt" "$help" "$uninstallOpt" "$end")
  
  # execute in subshell so exit code doesn't exit the script
  (menu "${options[@]}") && true
  result="${options[$?]}"

  case $result in
    $help) showHelpAndExit;;
    $imageOpt) handleImageMenu;;
    $uninstallOpt) handleUninstall;;
    $shellOpt|$autoloaderOpt|$configOpt|$runOpt|$releaseOpt)
      # remove " Container" and set as currentn container
      container=$(echo "${result/ Container/}")
      handleContainerMenu
      ;;
    * ) exit;;
  esac
}

#                   *******************                   #
# *******************      main       ******************* #
#                   *******************                   #

# figure out why we're running the script
processArgs $@

# exit if `docker` command not available
checkDocker

# make sure the base image has been built
promptBuildImageIfNotExists

# main switchboard to act depending on which positionl arg was passed

if [[ "$positional" ]]; then
  case $positional in
    image) handleImageCLI;;
    shell|config|run|autoloader|releaseBuild) handleContainerCLI;;
    *) exitUnexpectedPositionalArgs;;
  esac
else
  handleMainMenu
fi
