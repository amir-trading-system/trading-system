import elasticsearch


class Client:
    def __init__(
        self,
    ):
        self.host = "http://localhost:9200"

    def connect(
        self,
    ) -> elasticsearch.Elasticsearch:
        return elasticsearch.Elasticsearch(
            hosts=[self.host],
        )
