# BEGIN-INCLUDE ./src/bash_version_check.bash 
((BASH_VERSINFO<4 || BASH_VERSINFO==4 && BASH_VERSINFO[1]<4)) && \
    echo >&2 "bash $BASH_VERSION is too old. Please install bash 4.4 or newer." && \
    exit 1

# END-INCLUDE 
# BEGIN-INCLUDE ./src/logging.bash 
## ### `ocrd__raise`
## 
## Raise an error and exit.
ocrd__raise () {
    echo >&2 "ERROR: $1"; exit 127
}

## ### `ocrd__log`
## 
## Delegate logging to `ocrd log`
ocrd__log () {
    local log_level="${ocrd__argv[log_level]:-}"
    if [[ -n "$log_level" ]];then
        ocrd -l "$log_level" log "$@"
    else
        ocrd log "$@"
    fi
}


## ### `ocrd__minversion`
## 
## Ensure minimum version
# ht https://stackoverflow.com/posts/4025065
ocrd__minversion () {
    local minversion="$1"
    local version=$(ocrd --version|sed 's/ocrd, version //')
    #echo "$minversion < $version?"
    local IFS=.
    version=($version)
    minversion=($minversion)
    # MAJOR > MAJOR
    if (( ${version[0]} > ${minversion[0]} ));then
        return
    # MAJOR == MAJOR
    elif (( ${version[0]} == ${minversion[0]} ));then
        # MINOR > MINOR
        if (( ${version[1]} > ${minversion[1]} ));then
            return
        # MINOR == MINOR
        elif (( ${version[1]} == ${minversion[1]} ));then
            # PATCH > PATCH
            if (( ${version[2]} >= ${minversion[2]} ));then
                return
            fi
        fi
    fi
    ocrd__raise "ocrd/core is too old (${version[*]} < ${minversion[*]}). Please update OCR-D/core"
}

# END-INCLUDE 
# BEGIN-INCLUDE ./src/dumpjson.bash 
## ### `ocrd__dumpjson`
## 
## Output ocrd-tool.json.
## 
## Requires `$OCRD_TOOL_JSON` and `$OCRD_TOOL_NAME` to be set:
## 
## ```sh
## export OCRD_TOOL_JSON=/path/to/ocrd-tool.json
## export OCRD_TOOL_NAME=ocrd-foo-bar
## ```
## 
ocrd__dumpjson () {
    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" dump
}

# END-INCLUDE 
# BEGIN-INCLUDE ./src/usage.bash 
## ### `ocrd__usage`
## 
## Print usage
## 
ocrd__usage () {

    ocrd ocrd-tool "$OCRD_TOOL_JSON" tool "$OCRD_TOOL_NAME" help

}

# END-INCLUDE 
# BEGIN-INCLUDE ./src/parse_argv.bash 
## ### `ocrd__parse_argv`
## 
## Expects an associative array ("hash"/"dict") `ocrd__argv` to be defined:
## 
## ```sh
## declare -A ocrd__argv=()
## ```
ocrd__parse_argv () {

    # if [[ -n "$ZSH_VERSION" ]];then
    #     print -r -- ${+ocrd__argv} ${(t)ocrd__argv}
    # fi
    if ! declare -p "ocrd__argv" >/dev/null 2>/dev/null ;then
        ocrd__raise "Must set \$ocrd__argv (declare -A ocrd__argv)"
    fi

    if ! declare -p "params" >/dev/null 2>/dev/null ;then
        ocrd__raise "Must set \$params (declare -A params)"
    fi

    ocrd__argv[overwrite]=false

    local __parameters=()
    local __parameter_overrides=()

    while [[ "${1:-}" = -* ]];do
        case "$1" in
            -l|--log-level) ocrd__argv[log_level]=$2 ; shift ;;
            -h|--help|--usage) ocrd__usage; exit ;;
            -J|--dump-json) ocrd__dumpjson; exit ;;
            -p|--parameter) __parameters+=(-p "$2") ; shift ;;
            -P|--parameter-override) __parameter_overrides+=(-P "$2" "$3") ; shift ; shift ;;
            -g|--page-id) ocrd__argv[page_id]=$2 ; shift ;;
            -O|--output-file-grp) ocrd__argv[output_file_grp]=$2 ; shift ;;
            -I|--input-file-grp) ocrd__argv[input_file_grp]=$2 ; shift ;;
            -w|--working-dir) ocrd__argv[working_dir]=$(realpath "$2") ; shift ;;
            -m|--mets) ocrd__argv[mets_file]=$(realpath "$2") ; shift ;;
            --overwrite) ocrd__argv[overwrite]=true ;;
            -V|--version) ocrd ocrd-tool "$OCRD_TOOL_JSON" version; exit ;;
            *) ocrd__raise "Unknown option '$1'" ;;
        esac
        shift
    done

    if [[ ! -r "${ocrd__argv[mets_file]:=$PWD/mets.xml}" ]];then
        ocrd__usage
        exit 1
    fi

    if [[ ! -d "${ocrd__argv[working_dir]:=$(dirname "${ocrd__argv[mets_file]}")}" ]];then
        ocrd__raise "workdir '${ocrd__argv[working_dir]}' not a directory. Use -w/--working-dir to set correctly"
    fi

    if [[ ! "${ocrd__argv[log_level]:=INFO}" =~ OFF|ERROR|WARN|INFO|DEBUG|TRACE ]];then
        ocrd__raise "log level '${ocrd__argv[log_level]}' is invalid"
    fi

    if [[ -z "${ocrd__argv[input_file_grp]:=}" ]];then
        ocrd__raise "Provide --input-file-grp/-I explicitly!"
    fi

    if [[ -z "${ocrd__argv[output_file_grp]:=}" ]];then
        ocrd__raise "Provide --output-file-grp/-O explicitly!"
    fi

    local params_parsed retval
    params_parsed="$(ocrd ocrd-tool "$OCRD_TOOL_JSON" tool $OCRD_TOOL_NAME parse-params "${__parameters[@]}" "${__parameter_overrides[@]}")" || {
        retval=$?
        ocrd__raise "Failed to parse parameters (retval $retval):
$params_parsed"
    }
    eval "$params_parsed"

}

# END-INCLUDE 
# BEGIN-INCLUDE ./src/wrap.bash 
ocrd__wrap () {

    declare -gx OCRD_TOOL_JSON="$1"
    declare -gx OCRD_TOOL_NAME="$2"
    shift
    shift
    declare -Agx params
    params=()
    declare -Agx ocrd__argv
    ocrd__argv=()

    if ! which "ocrd" >/dev/null 2>/dev/null;then
        ocrd__raise "ocrd not in \$PATH"
    fi

    if ! declare -p "OCRD_TOOL_JSON" >/dev/null 2>/dev/null;then
        ocrd__raise "Must set \$OCRD_TOOL_JSON"
    elif [[ ! -r "$OCRD_TOOL_JSON" ]];then
        ocrd__raise "Cannot read \$OCRD_TOOL_JSON: '$OCRD_TOOL_JSON'"
    fi

   if [[ -z "$OCRD_TOOL_NAME" ]];then
        ocrd__raise "Must set \$OCRD_TOOL_NAME"
    elif ! ocrd ocrd-tool "$OCRD_TOOL_JSON" list-tools|grep -q "$OCRD_TOOL_NAME";then
        ocrd__raise "No such command \$OCRD_TOOL_NAME: $OCRD_TOOL_NAME"
    fi

    ocrd__parse_argv "$@"

}

# END-INCLUDE 
