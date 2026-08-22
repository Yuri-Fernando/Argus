"""api/services/ — business logic backing `api/routes/`, reading the on-disk data products
(`data/mdm/`, `data/ml/`) and reusing `snowflake/local_runner.py` for platform metrics rather
than recomputing them.
"""
