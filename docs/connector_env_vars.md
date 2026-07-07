## Connector Environment Variables

| Connector | Env Var | Required | Default |
|---|---|---|---|
| FRED Commodity | `FRED_API_KEY` | For live PPI data | Mock prices |
| OpenMeteo Weather | `WEATHER_LIVE` | No; set `false` to force mock/cache fallback | Live, free |
| Toast POS | `TOAST_CLIENT_ID`, `TOAST_CLIENT_SECRET` | For live POS | Mock data |
| Toast POS optional | `TOAST_BASE_URL`, `TOAST_LOCATION_ID` | Optional live configuration | Toast API default URL, empty location |
| QuickBooks Online | `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REALM_ID` | For live accounting | Mock data |
| QuickBooks Online optional | `QBO_REFRESH_TOKEN`, `QBO_SANDBOX` | Optional live configuration | Empty refresh token, sandbox enabled |
| Snowflake | `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD` | For live metadata | Mock data |
| Snowflake optional | `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_SCHEMA` | Optional live configuration | Empty database/warehouse, `PUBLIC` schema |
| dbt Cloud | `DBT_API_TOKEN`, `DBT_ACCOUNT_ID` | For live models | Mock data |
| dbt local artifacts | `DBT_ARTIFACTS_PATH` | Optional when `DBT_API_TOKEN` is set | No artifact path |
| Airflow | `AIRFLOW_BASE_URL`, `AIRFLOW_USER`, `AIRFLOW_PASSWORD` | For live DAGs | Mock data |
| Airflow optional | `AIRFLOW_TOKEN` | Optional bearer-token auth | Empty token |
