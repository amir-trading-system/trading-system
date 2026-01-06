import elasticsearch


class Client:
    def __init__(
        self,
    ):
        self.host = "https://localhost:9200"
        self.username = "elastic"
        self.password = "4obla=pJpXkiaeAglNQH"
        self.certs_file_path = "logger/elasticsearch/ca_certs.crt"

    def connect(
        self,
    ) -> elasticsearch.Elasticsearch:
        return elasticsearch.Elasticsearch(
            hosts=[self.host],
            ca_certs=self.certs_file_path,
            basic_auth=(
                self.username,
                self.password,
            ),
        )
