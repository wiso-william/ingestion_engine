from ingestion_engine import Column, TableConfig

# jsonplaceholder returns geo.lat and geo.lng as JSON strings, yet they are
# declared as Float64: the ClickHouse driver parses a numeric string into the
# declared numeric type, so the destination holds real floats. See the
# Limitations section of the README for what is and is not converted.
users = TableConfig(
    name="users",
    columns=[
        Column("id", "UInt64", "id"),
        Column("name", "String", "name"),
        Column("username", "String", "username"),
        Column("email", "String", "email"),
        Column("street", "String", "address.street"),
        Column("suite", "String", "address.suite"),
        Column("city", "String", "address.city"),
        Column("zipcode", "String", "address.zipcode"),
        Column("lat", "Float64", "address.geo.lat"),
        Column("lng", "Float64", "address.geo.lng"),
        Column("phone", "String", "phone"),
        Column("website", "String", "website"),
        Column("company_name", "String", "company.name"),
        Column("company_catch_phrase", "String", "company.catchPhrase"),
        Column("company_bs", "String", "company.bs"),
    ],
    order_by="id",
    source="json_placeholder__users",
)
