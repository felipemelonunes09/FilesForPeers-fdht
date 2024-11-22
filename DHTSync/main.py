import logging
import threading
import globals
import yaml
import socket
import pickle
import json

class Server():
    
    hashtable: dict                 = dict()
    configuration: dict[str, dict]  = dict()
    logger: logging.Logger          = logging.getLogger(__name__)
    
    class ClientConnectionThread():
        pass
    class ServerConnectionThread():
        pass
    
    class RequestUDHTThread(threading.Thread):
        def __init__(self, udht_connection: tuple[str, int]) -> None:
            self.udht_connection = udht_connection
            super().__init__()
            
        def run(self) -> None:
            try:
                Server.logger.info('RequestUDHTThread started')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(self.udht_connection)
                sock.send(json.dumps({'message_type': 2}).encode(globals.ENCODING))
                hash_bin = sock.recv(1024)
                Server.hashtable = pickle.loads(hash_bin)
                Server.logger.info('RequestUDHTThread finished --resolution: builded hashtable and closing state')
                Server.logger.info(f'User Hash Table entries {len(Server.hashtable)}')
                sock.close()
                return super().run()
            except ConnectionRefusedError:
                Server.logger.error('Connection refused to UDHT')
            except socket.gaierror as e:
                Server.logger.error(f'Failed to connect to {self.udht_connection}: {e}')
            except socket.timeout as e:
                Server.logger.error(f"Socket timeout: {e}")
            except socket.error as e:
                Server.logger.error(f"Socket error message: {e}")

    
    def __init__(self) -> None:
        Server.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = logging.FileHandler(globals.LOG_NAME)
        handler.setFormatter(formatter)
        Server.logger.addHandler(handler)
    
    def start(self) -> None:
        self.logger.info('Server started')
        self.__read_config()
        self.__setup_hashtable()
        self.run()
    
    def run(self) -> None:
        self.logger.info('Server running')
    
    def __setup_hashtable(self) -> None:
        connection = (self.configuration['udht']['manager']['ip'], int(self.configuration['udht']['manager']['port']))
        thread = Server.RequestUDHTThread(udht_connection=connection)
        thread.start()
        thread.join()
    
    def __read_config(self) -> None:
        with open(globals.CONFIG_FILE, 'r') as file:
            self.configuration = yaml.safe_load(file)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server()
    server.start()
    server.run()

