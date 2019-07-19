#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
echo "add task to crontab..."
echo "*/1 * * * * export DISPLAY=:0 && /bin/bash ${DIR}/crontab_watch.sh" | crontab
