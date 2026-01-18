import elasticsearch


class Client:
    def __init__(
        self,
        username: str,
        password: str,
        certs_file_path: str,
    ):
        self.host = "https://localhost:9200"
        self.username = username
        self.password = password
        self.certs_file_path = certs_file_path

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
