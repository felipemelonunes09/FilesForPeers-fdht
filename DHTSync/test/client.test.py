import json
from socket import *

connection = ("0.0.0.0", 3001)

mock_dht = {
    '101.3.4.2': {'name': 'Felipe Nunes', 'ip': '101.3.4.2', 'port': '8001', 'createdAt': '2024-10-28 14:48:49.842886', 'lastConnectionOn': '2024-10-28 14:48:49.842892'},
    '101.3.4.3': {'name': 'Henry Miyawaki', 'ip': '101.3.4.2', 'port': '8001', 'createdAt': '2024-10-28 14:48:49.842886', 'lastConnectionOn': '2024-10-28 14:48:49.842892'},
    '101.3.4.5': {'name': 'Vinicius Miranda', 'ip': '101.3.4.2', 'port': '8001', 'createdAt': '2024-10-28 14:48:49.842886', 'lastConnectionOn': '2024-10-28 14:48:49.842892'},
    '101.3.4.6': {'name': 'Gabriel', 'ip': '101.3.4.2', 'port': '8001', 'createdAt': '2024-10-28 14:48:49.842886', 'lastConnectionOn': '2024-10-28 14:48:49.842892'}
}

socket = socket(AF_INET, SOCK_STREAM)
socket.connect(connection)
socket.sendall(json.dumps(mock_dht).encode('utf-8'))

