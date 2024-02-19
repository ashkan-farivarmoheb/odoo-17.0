#!/bin/bash

set -e

if [ -v PASSWORD_FILE ]; then
    PASSWORD="$(< $PASSWORD_FILE)"
fi

# set the postgres database host, port, user and password according to the environment
# and pass them as arguments to the odoo process if not present in the config file
: ${HOST:=${DB_PORT_5432_TCP_ADDR:='db'}}
: ${PORT:=${DB_PORT_5432_TCP_PORT:=5432}}
: ${USER:=${DB_ENV_POSTGRES_USER:=${POSTGRES_USER:='odoo'}}}
: ${PASSWORD:=${DB_ENV_POSTGRES_PASSWORD:=${POSTGRES_PASSWORD:='odoo'}}}
: ${RESTORE_FROM_BACKUP:="true"}

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Check if restoration from backup is enabled via an environment variable
# Check if restoration from backup is enabled via an environment variable
if [ "${RESTORE_FROM_BACKUP}" = "true" ]; then
    echo "Restoration from backup is enabled."

    # Define the backup directory and the destination directory
    BACKUP_DIR="/etc/odoo/resources/backupFiles"
    DEST_DIR="/mnt/efs/data"

    # Find the latest modified zip file in the backup directory
    LATEST_ZIP=$(find "$BACKUP_DIR" -type f -name '*.zip' | sort -n | tail -1)

    # Proceed only if a latest zip file is found
    if [[ -n "$LATEST_ZIP" ]]; then
        echo "Latest backup zip found: $LATEST_ZIP"
        
        # Create a temporary directory to unzip the contents
        TEMP_DIR=$(mktemp -d)
        
        # Unzip the file
        unzip -q "$LATEST_ZIP" -d "$TEMP_DIR"
        echo "Unzipped backup to $TEMP_DIR"
        
        # Copy the filestore folder if it exists
        if [[ -d "$TEMP_DIR/filestore" ]]; then
            echo "Copying filestore to $DEST_DIR"
            # Ensure the destination directory exists
            mkdir -p "$DEST_DIR"
            # Copy filestore
            cp -a "$TEMP_DIR/filestore/." "$DEST_DIR/"
        fi
        
        # Copy the dump.sql if it exists
        if [[ -f "$TEMP_DIR/dump.sql" ]]; then
            echo "Copying dump.sql to $BACKUP_DIR"
            cp "$TEMP_DIR/dump.sql" "$BACKUP_DIR/"
        fi
        
        # Clean up the temporary directory
        rm -rf "$TEMP_DIR"
    else
        echo "No backup zip file found in $BACKUP_DIR. Skipping restore operations."
    fi
else
    echo "Restoration from backup is not enabled. Skipping restore operations."
fi
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

DB_ARGS=()
function check_config() {
    param="$1"
    value="$2"
    if grep -q -E "^\s*\b${param}\b\s*=" "$ODOO_RC" ; then       
        value=$(grep -E "^\s*\b${param}\b\s*=" "$ODOO_RC" |cut -d " " -f3|sed 's/["\n\r]//g')
    fi;
    DB_ARGS+=("--${param}")
    DB_ARGS+=("${value}")
}
check_config "db_host" "$HOST"
check_config "db_port" "$PORT"
check_config "db_user" "$USER"
check_config "db_password" "$PASSWORD"

case "$1" in
    -- | odoo)
        shift
        if [[ "$1" == "scaffold" ]] ; then
            exec odoo "$@"
        else
            wait-for-psql.py ${DB_ARGS[@]} --timeout=30
            exec odoo "$@" "${DB_ARGS[@]}"
        fi
        ;;
    -*)
        wait-for-psql.py ${DB_ARGS[@]} --timeout=30
        exec odoo "$@" "${DB_ARGS[@]}"
        ;;
    *)
        exec "$@"
esac

exit 1
