import socket, threading, time, string, json, os  # pyngrok
from random import choice
import torch
import fastai
from deoldify.visualize import *
if not torch.cuda.is_available():
    print('GPU not available.')
torch.backends.cudnn.benchmark = True

import warnings
warnings.filterwarnings("ignore")

chars = string.ascii_letters  + string.digits
HOST = "127.0.0.1"  # localhost 127.0.0.1
PORT = 65432  # Port to listen on 65432
BufferSize = 1024 * 1024
clientsById = {}
EndSym = b"_*<end>*_"
MesSym = b"_*<mes>*_"
ByteEndSym = b"_*<endSending>*_"
class Client():
    def __init__(self, conn, addr, id):
        self.Conn = conn
        self.Addr = addr
        self.Id = id


def AcceptHandler():
    while True:
        conn, addr = s.accept()
        id = ""
        for i in range(8):
            id += id.join(choice(chars))
        client = Client(conn, addr, id)
        clientsById[id] = client
        print(f"Connected by {addr[0]}:{addr[1]}")
        recvHandler = threading.Thread(target=RecvHandler, args=(client,))
        recvHandler.daemon = True
        recvHandler.start()

def disconnectClients(client):
    print("Клиент удалён!")
    clientsById.pop(client.Id)
    client.Conn.close()




def RecvHandler(client):
    RunRecv = True
    buffer = b""
    msg = None
    data = client.Conn.recv(BufferSize)
    print(data)
    if not (data == b'im client'):
        disconnectClients(client)
        return
    else:
        client.Conn.sendall(b"molodec xoroshiy client")
        while RunRecv: 
            chunk = client.Conn.recv(BufferSize)
            if chunk == b"":
                disconnectClients(client)
                RunRecv = False
                break

            raw_data = buffer + chunk

            while raw_data.find(EndSym) != -1: # вырезка сообщения из буфера
                startPos = raw_data.find(MesSym) # "_*mes*_{}..."
                endPos = raw_data.find(EndSym) + len(EndSym) # "...{}_*end*_"
                cutted = raw_data[startPos:endPos] # вырезаем
                raw_data = raw_data[:startPos] + raw_data[endPos:]

                raw_msg = cutted[len(MesSym):-len(EndSym)] # "{}"
                print(raw_msg)
                msg = json.loads(raw_msg.decode("utf-8"))
                print(msg)


            else: # если не нашли конечного символа то...
                buffer = raw_data
                bytesEndIndex = buffer.find(ByteEndSym) # находим байт индекс
                if bytesEndIndex != -1:
                    fileData = buffer[:bytesEndIndex] # получаем байты

                    buffer = buffer[bytesEndIndex+len(ByteEndSym):] # удаление данных
                    with open("ServerDownloads\\" + msg["name"], "wb") as file:
                        file.write(fileData)

                    print("файл скачан")
                    break

                # b'{"name":"hue.jpg", "size":12321}'
        print("начинаю обработку")
        if msg['type'] == "Art🌁":
            colorizer = get_image_colorizer(artistic=True,stats=([0.7137, 0.6628, 0.6519],[0.2970, 0.3017, 0.2979]))
            colorizer.plot_transformed_image("ServerDownloads\\" + msg['name'], render_factor=msg["render_factor"], display_render_factor=True, watermarked=False, post_process=True, figsize=(8,8)) # Image
            with open(f'result_images\\{msg["name"]}', "rb") as f:
                data = f.read()
            print("отправка обработаного изобрадения")
            client.Conn.sendall(data+EndSym)



        elif msg['type'] == "Photo🌄":
            colorizer = get_image_colorizer(artistic=False,stats=([0.7137, 0.6628, 0.6519],[0.2970, 0.3017, 0.2979]))
            colorizer.plot_transformed_image("ServerDownloads\\" + msg['name'], render_factor=msg["render_factor"], display_render_factor=True, watermarked=False, post_process=True, figsize=(8,8)) # Image
            with open(f'result_images\\{msg["name"]}', "rb") as f:
                data = f.read()
            print("отправка обработаного изобрадения")
            client.Conn.sendall(data+EndSym)

            #colorizer = get_image_colorizer(artistic=,stats=([0.7137, 0.6628, 0.6519],[0.2970, 0.3017, 0.2979]))

if __name__ == "__main__":
    print(f"сервер запущен на {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    acceptThread = threading.Thread(target=AcceptHandler)
    acceptThread.deamon = True
    acceptThread.start()
    
