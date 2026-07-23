from ingestion_engine.models.schema import Column, TableConfig

esami_categorie = TableConfig(
    name="esami_categorie",
    columns=[
        Column("id", "UInt8", "id"),
        Column("descrizione", "String", "descrizione"),
        Column("descrizione_breve", "String", "descrizione_breve"),
        Column("medical_area", "Nullable(String)", "medical_area"),
    ],
    order_by="id",
    source="json_placeholder__users"
)