import collector
import database

if __name__ == "__main__":
    database_client = database.client.Client()
    collector = collector.stocks_data_collector.Collector(
        database_client=database_client,
        tws_host="localhost",
        tws_port=8081,
    )
    collector.collect(
        timeframe=5,
    )
