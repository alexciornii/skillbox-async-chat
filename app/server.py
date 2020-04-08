#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from collections import namedtuple


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
            self.save_history(decoded)
        else:
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                if temp_login in [client.login for client in self.server.clients]:
                    self.transport.write(f"Логин {temp_login} занят, попробуйте другой\n".encode())
                    self.connection_lost(None)
                else:
                    self.login = temp_login
                    self.send_history()
                    self.transport.write(f"Привет, {self.login}!\n".encode())
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for msg in self.server.history[9::-1]:
            self.transport.write(f"{msg['login']}:{msg['message']}".encode())
     
    def save_history(self, message):
        self.server.history.insert(0, {"login": self.login, "message": message})
        

class Server:
    clients: list
    history: []

    History = namedtuple("History", "login, message")
    
    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
