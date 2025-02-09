from connectors import interactive_brokers

if __name__ == "__main__":
    c = interactive_brokers.Connector()
    c.connect()
    print("Hello")
