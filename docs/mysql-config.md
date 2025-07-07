# MySQL Configuration

The optional `config.py` module includes a `MYSQL_CONFIG` dictionary for connecting to a MySQL database. Beginning with this version, connection details are read from environment variables so credentials do not have to be stored in the source code.

## Required variables

Set the following variables in your shell or in a `.env` file before running the application:

```bash
export MYSQL_HOST="localhost"
export MYSQL_DATABASE="effinova_db"
export MYSQL_USER="root"
export MYSQL_PASSWORD="password"
# Optional
export MYSQL_PORT="3306"
export MYSQL_CHARSET="utf8mb4"
export MYSQL_COLLATION="utf8mb4_unicode_ci"
export MYSQL_AUTOCOMMIT="True"
```

Default values (shown above) are used when a variable is not defined, which makes local development simple. For production deployments, be sure to provide secure values for `MYSQL_USER` and `MYSQL_PASSWORD`.
