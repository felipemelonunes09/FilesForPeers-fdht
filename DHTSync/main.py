from abc import ABC, abstractmethod
from typing import Any
import datetime
import logging
import threading
import globals
import yaml
import socket
import pickle
import json

class HashTableConnection(ABC):
    @abstractmethod
    def send_hashtable_entry(self, *args, **kwds) -> None:
        pass
            
    @abstractmethod
    def receive_hashtable(self, payload: Any) -> dict[str, dict]:
        pass

## This class refers not with a connection with the peer but a connnection 
## with the microservice to load the user hashtable
class TCPHashtableConnection(HashTableConnection):
    def __init__(self, address: tuple[str, int], encoding: str = globals.ENCODING) -> None:
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__address = address
        self.__encoding = encoding
        self.__keep_alive = False
        self.__connected = False
        
    def receive_hashtable(self, payload: dict | None) -> dict[str, dict]:
        if self.__connected == False:
            Server.logger.info(f'Attemping tcp-connection to: {self.__address}')
            self.__sock.connect(self.__address)
            self.__connected = True
        if payload:
            Server.logger.info(f'Sending {payload} with tcp-connection to: {self.__address} with encoding {self.__encoding}')
            self.__sock.sendall(json.dumps(payload).encode(self.__encoding))
        hashtable = self.__sock.recv(1024)
        if self.__keep_alive:
            self.__sock.close()
            self.__connected = False
        return pickle.loads(hashtable)
    
    def send_hashtable_entry(self, payload: str) -> None:
        if self.__connected == False:
            Server.logger.info(f'Attemping tcp-connection to: {self.__address}')
            self.__sock.connect(self.__address)
            self.__connected = True
        self.__sock.connect(self.__address)
        self.__sock.send(payload.encode(self.__encoding))
        if self.__keep_alive:
            self.__sock.close()
            self.__connected = False
        
    def set_keep_alive(self, keep: bool) -> None:
        self.keep_alive = keep
        

class Server():
    class ConnectionPool():
        class ConnectionThread(threading.Thread):
            def __init__(self, connection: socket.socket, address: tuple[str, int], hashtable: dict[str, dict]) -> None:
                self.__connection = connection
                self.__adress = address
                self.hashtable = hashtable
                super().__init__()
            
            def get_adress(self) -> tuple[str, int]:
                return self.__adress
            
            def get_connection(self) -> socket.socket:
                return self.__connection
            
            def run(self) -> None:
                Server.ConnectionPool.remove_thread(id(self))
            
        class ClientConnectionThread(ConnectionThread):
            def run(self) -> None:
                Server.logger.info(f"Starting client connection thread sync with: {self.get_adress()}")
                conn = self.get_connection()
                data = conn.recv(1024)
                decoded_hashtable = json.loads(data.decode(globals.ENCODING))
                encoded_hashtable = json.dumps(self.hashtable).encode(globals.ENCODING)
                conn.sendall(encoded_hashtable)
                Server.merge_hashtables(decoded_hashtable)
                Server.logger.warning(f"Finished hashtable merge --hashtable not persisted await for the next job schedule")
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
        
        @staticmethod
        def remove_thread(id: str) -> None:
            with Server.ConnectionPool.__lock:
                Server.ConnectionPool.__pool.remove(id)
            
        def run(self) -> None:
            try:
                Server.logger.info('RequestUDHTThread started')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(self.dht_connection)
                sock.send(json.dumps({'message_type': 2}).encode(globals.ENCODING))
                hash_bin = sock.recv(1024)
                Server.hashtable = pickle.loads(hash_bin)
                Server.logger.info('RequestUDHTThread finished --resolution: builded hashtable and closing state')
                Server.logger.info(f'User Hash Table entries {len(Server.hashtable)}')
                sock.close()
                return super().run()
            except ConnectionError as e:
                Server.logger.info(f'RequestUDHTThread finished --resolution: connection error: {e}')
            except ConnectionRefusedError as e:
                Server.logger.info(f'RequestUDHTThread finished --resolution: connection refused: {e}')
    
    class DHTThreadRequest(threading.Thread):
        def __init__(self, connection: HashTableConnection):
            self.__connection = connection
            super().__init__()
            
        def get_connection(self) -> HashTableConnection:
            return self.__connection
        
        def run(self) -> None:
            try:
                Server.logger.info('RequestUDHTThread started')
                connection = self.get_connection()
                hashtable = connection.receive_hashtable(payload={'message_type': 2})
                Server.hashtable = hashtable
                Server.logger.info('RequestUDHTThread finished --resolution: builded hashtable and closing state')
                Server.logger.info(f'User Hash Table entries {len(Server.hashtable)}')
                super().run()
            except ConnectionRefusedError as e:
                Server.logger.info(f'RequestUDHTThread finished --resolution: connection-refused: {e}')
            except ConnectionError as e:
                Server.logger.info(f'RequestUDHTThread finished --resolution: connection-error: {e}')

    
    hashtable: dict[str, dict]      = dict()
    configuration: dict[str, dict]  = dict()
    changes: dict[str, dict]        = dict()
    logger: logging.Logger          = logging.getLogger(__name__)
    thread_pool: ConnectionPool     = ConnectionPool()
    diff_count: int                 = 0
    changes: set[str]               = set()
    
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
        self.logger.info(f'Listening on {connection}')
        pool_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pool_socket.bind(connection)
        pool_socket.listen(globals.SOCKET_CONNECTION_LIMIT)
        
        while True:
            in_connection, in_address = pool_socket.accept()
            self.logger.info(f'Incoming connection from {in_address}')
            client_thread = Server.ConnectionPool.ClientConnectionThread(in_connection, in_address, Server.hashtable)
            self.thread_pool.add_connection_thread(client_thread)
    
    def __setup_hashtable(self) -> None:
        connection = (self.configuration['udht']['manager']['ip'], self.configuration['udht']['manager']['port'])
        thread = Server.DHTThreadRequest(connection=TCPHashtableConnection(connection))
        thread.start()
        thread.join()
    
    def __read_config(self) -> None:
        with open(globals.CONFIG_FILE, 'r') as file:
            self.configuration = yaml.safe_load(file)
            
    @staticmethod
    def merge_hashtables(peer_hashtable: dict[str, dict]) -> None:
        unique_keys   = set(peer_hashtable)-set(Server.hashtable)
        conflict_keys = set(peer_hashtable.keys()) & set(Server.hashtable.keys())
        Server.logger.info(f"Peer diff: {len(unique_keys)} entries")
        Server.logger.info(f"Peer conflict: {len(conflict_keys)} entries")
        for key in unique_keys:
            Server.hashtable[key] = peer_hashtable[key]
            Server.diff_count += 1
            Server.logger.info(f"Added peer {key} to in-memory hashtable --diff: {Server.diff_count}")
            
        for key in conflict_keys:
            Server.logger.info(f"Peer conflict: {key} --resolution: 002.1")
            client_updated_at = peer_hashtable.get(key).get('updatedAt')
            server_updated_at = Server.hashtable.get(key).get('updatedAt')
            client_updated_at = datetime.datetime.strptime(client_updated_at, '%Y-%m-%d %H:%M:%S.%f')
            server_updated_at = datetime.datetime.strptime(server_updated_at, '%Y-%m-%d %H:%M:%S.%f')
            
            if client_updated_at > server_updated_at: 
                Server.diff_count += 1
                Server.logger.info(f"Updated peer {key} to in-memory hashtable --diff: {Server.diff_count}")
                Server.hashtable[key] = peer_hashtable[key]
                Server.changes.add(key)
        
        Server.logger.info(f"Finished hashtable merge in-memory-hashtable: {len(Server.hashtable)} entries")
                
                         

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server()
    server.start()