import elasticsearch


class Client:
    def __init__(
        self,
    ):
        self.host: str = "http://localhost:9200"

    def delete_older_logs(
        self,
    ):
        with elasticsearch.Elasticsearch(
            hosts=[self.host],
        ) as es_client:
            es_client.delete_by_query(
                index="ds-day_trading*",
            )
