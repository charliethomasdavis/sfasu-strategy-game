"""
File: network.py
Programmers: Fernando Rodriguez, Charles Davis, Paul Rogers


Contains the Network class which adds connectivity to a client.

"""

import socket
import pickle

from src.encryption import encrypt, decrypt
from src.gamestate import GameState

class Network:
    """
    Adds network functionality to the game.
    Allows sending and receiving encrypted data.
    """

    # Initilization
    def __init__(self, server_host, server_port):
        self.CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = server_host
        self.PORT = server_port
        self.ADDR = (self.HOST, self.PORT)
        self.player_num = None

        gamestate = GameState()

    def get_gamestate(self):
        self.send_command("get")
        return self.receive_pickle()

    def send_command(self, data):
        # Send data to server
        try:
            encrypted_data = encrypt(data.encode())
            self.CLIENT.sendall(encrypted_data)
        except socket.error as e:
            print(str(e))

    def send_pickle(self, data):
        # Send move or attack to server
        data_pickle = pickle.dumps(data)
        try:
            encrypted_data = encrypt(data_pickle)
            self.CLIENT.sendall(encrypted_data)
        except socket.error as e:
            print(str(e))

    def send_move(self, move):
        self.send_command("move")
        self.receive() #TODO: Seeing if we need to receive before sending again
        self.send_pickle(move)

    def send_attack(self, attack):
        self.send_command("attack")
        self.send_pickle(attack)

    def receive_pickle(self):
        """
        Retrieve pickle from server.
        
        Returns:
            {object} -- An object loaded from pickle
        """
        try:
            decrypted_data = decrypt(self.CLIENT.recv(1024))
            return pickle.loads(decrypted_data)
        except socket.error as e:
            print(str(e))
            return None

    def receive(self):
        try:
            decrypted_data = decrypt(self.CLIENT.recv(2014))
            data = decrypted_data.decode()
            return data
        except socket.error as e:
            print(str(e))
            return None

    def receive_player_num(self):
        try:
            player_num = int(self.receive())
            return player_num
        except ValueError as e:
            print(str(e))
            return None

    def connect(self):
         # Connect to server
        self.CLIENT.connect(self.ADDR)
        self.player_num = self.receive_player_num()
        print("Connected to server:", self.HOST)

    def get_player_num(self):
        return self.player_num

    def close(self):
        # Close CLIENT socket
        self.CLIENT.close()