import logging
import threading
import globals
import yaml
import socket
import pickle
import json

class Server():
    class ConnectionPool():
        class ConnectionThread(threading.Thread):
            def __init__(self, connection: socket.socket, address: tuple[str, int]) -> None:
                self.__connection = connection
                self.__adress = address
                super().__init__()
                
            def run(self) -> None:
                Server.ConnectionPool.__pool.remove(id(self))
            
        class ClientConnectionThread(ConnectionThread):
            def run(self) -> None:
                return super().run()
            
        class ServerConnectionThread(ConnectionThread):
            def run(self) -> None:
                return super().run()
            
        __pool: set[int] = set()
        __lock: threading.Lock = threading.Lock()
        __limit: int = globals.THREAD_POOL_LIMIT
            
        def add_connection_thread(self, thread: ConnectionThread) -> bool:
            with self.__lock:
                if len(self.__pool) < self.__limit:
                    self.__pool.add(id(thread))
                    thread.start()
                    return True
                return False
    
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

    hashtable: dict                 = dict()
    configuration: dict[str, dict]  = dict()
    logger: logging.Logger          = logging.getLogger(__name__)
    thread_pool: ConnectionPool     = ConnectionPool()
    
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
        self.logger.info('Server running on listen mode...')
        connection  = (self.configuration['fdht']['sync']['ip'], self.configuration['fdht']['sync']['port'])
        pool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pool_socket.bind(connection)
        pool_socket.listen(globals.SOCKET_CONNECTION_LIMIT)
        
        while True:
            in_connection, in_address = pool_socket.accept()
            self.logger.info(f'Incoming connection from {in_address}')
            client_thread = Server.ConnectionPool.ClientConnectionThread(in_connection, in_address)
    
    def __setup_hashtable(self) -> None:
        connection = (self.configuration['udht']['manager']['ip'], self.configuration['udht']['manager']['port'])
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

