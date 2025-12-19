import collector

if __name__ == "__main__":
    collector = collector.stocks_data_collector.Collector(
        tws_host="localhost",
        tws_port=8081,
    )
    collector.collect()
