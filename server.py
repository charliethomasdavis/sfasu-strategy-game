"""
File: server.py
Programmers: Fernando Rodriguez, Charles Davis

Controls the connection between two clients.

"""
import socket
import sys
import threading
import pickle

from src.encryption import encrypt, decrypt
from src.gamestate import GameState

# Number of clients connected
client_count = 0

# Global gamestate object holding
# positions of player units and
# other game information.
gamestate = None

def start_server():
    """
    Sets up server and begins listening for
    client connections.
    """

    # Use the global variables
    global gamestate
    global client_count

    # Create a socket object
    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Use localhost and grab port from commandline arg
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])

    # Attempt bind to (host, port) pair
    try:
        SERVER.bind((HOST, PORT))
    except socket.error:
        print("Binding to " + HOST + ":" + str(PORT) + " failed.")
        SERVER.close()
        sys.exit()

    # Start listeing for connections, max of two
    SERVER.listen(2)
    print("Server listening on " + HOST + ":" + str(PORT))

    # Main server loop
    while True:
        if client_count < 2:
            # Accept incoming connection
            print("Waiting for client {}...".format(client_count + 1))
            connection, address = SERVER.accept()
            print("Established connection with " + address[0] + ":" + str(address[1]))

            # Increment global client counter
            client_count += 1
            # Keep track of whose turn it is
            player_num = 1

            if client_count == 1:
                # Create new gamestate object
                gamestate = GameState()
            else:
                # One client already connected so
                # this connection will be player 2
                player_num = 2

            # Create thread to handle client
            t = threading.Thread(target=client_thread, args=(connection, player_num))
            t.start()

        if client_count < 2 and gamestate.ready():
            # Game over, exit loop
            break

    print("\nServer closing...")
    SERVER.close()

##############   Client Loop   #################

def client_thread(connection, player_num):
    """
    Handles connection to clients.

    Sends player_num to client and then
    enters a loop where commands are 
    received from client and processed.

    Arguments:
        connection {socket} -- Used to access network
        player_num {int} -- Defines player order
    """

    # Access global variables
    global client_count
    global gamestate

    # Send player's number to client
    send_data(player_num, connection)

    # Track number of active threads
    thread_count = threading.active_count()
    print("[Debug]: Active threads:", thread_count)

    while True:
        # Receive one kB of data from client
        data = receive(connection)
        if data:
            if data == "get":
                send_gamestate(gamestate, connection)
            elif data == "turn":
                # Recieve a turn from client
                send_data("ok", connection)
                turn = None
                while not turn:
                    turn = receive_pickle(connection)
                send_data("ok", connection)
                # Turn consists of a move and an attack
                move = turn["move"]
                attack = turn["attack"]
                if move:
                    gamestate.move_unit(move)
                if attack:
                    gamestate.attack_unit(attack)
                    gamestate.determine_if_game_over()
                # Change player turn
                gamestate.change_turns()
            elif data == "request_turn":
                turn = gamestate.get_turn()
                send_data(turn, connection)
            elif data == "hand":
                send_data("ok", connection)
                hand = receive_pickle(connection)
                while not isinstance(hand, int):
                    hand = receive_pickle(connection)
                send_data("ok", connection)
                gamestate.set_hand(player_num, hand)
            elif data == "rps_winner":
                winner = gamestate.determine_rps_winner()
                send_data(winner, connection)
            elif data == "check_rps":
                in_session = gamestate.rps_in_session()
                send_data(in_session, connection)
            elif data == "start":
                send_data("ok", connection)
                gamestate.set_ready(player_num)
            elif data == "reset":
                gamestate.reset()
            elif data == "quit":
                break  # Exit main client loop to close connection
            else:
                print("[Error]: Received invalid command from player", player_num)
        else:
            # Data wasn't received; exit loop
            break

    # Close connection
    print("Closing connection with player", player_num)
    client_count -= 1
    if client_count == 0:
        # Delete gamestate object
        gamestate = None
        print("All clients disconnected.")
    connection.close()

################################################

def send_data(data, connection):
    try:
        encrypted_data = encrypt(str(data).encode())
        connection.sendall(encrypted_data)
    except socket.error as e:
        print("[Error]: Socket cannot be used to send data.")
        print(str(e))
    except TypeError:
        print("[Error]: Data cannot be converted to string to be sent.")

def send_gamestate(gamestate, connection):
    # Send gamestate as serialized pickle object
    gamestate_pickle = pickle.dumps(gamestate)
    try:
        encrypted_data = encrypt(gamestate_pickle)
        connection.sendall(encrypted_data)
    except socket.error as e:
        print(str(e))

def receive(connection):
    # Receive data from client
    try:
        decrypted_reply = decrypt(connection.recv(2048))
        reply = decrypted_reply.decode()
        return reply
    except socket.error as e:
        print(str(e))
        return None
    except UnicodeDecodeError as e:
        print("[Error]: Unable to decode message from client.")
        print(str(e))
        return None

def receive_pickle(connection):
    # Receive pickle object
    try:
        decrypted_reply = decrypt(connection.recv(2048))
        reply = pickle.loads(decrypted_reply)
        return reply
    except socket.error as e:
        print(str(e))
        return None

if __name__ == "__main__":
    # Check for correct number of arguments
    if len(sys.argv) < 3:
        print("Usage: python server.py <ip_address> <port>")
        sys.exit()
    # Enter server loop
    start_server()
