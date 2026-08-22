output "role_names" {
  description = "Map of logical role -> Snowflake role name, consumed by modules/snowflake/grants."
  value = {
    LOADER      = snowflake_account_role.loader.name
    TRANSFORMER = snowflake_account_role.transformer.name
    BI_READER   = snowflake_account_role.bi_reader.name
    AI_AGENT    = snowflake_account_role.ai_agent.name
  }
}
