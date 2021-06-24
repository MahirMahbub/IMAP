from __future__ import annotations

import email
import imaplib
import smtplib
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


#
class EmailData(BaseModel):
    user_name: str
    password: str
    imap_ssl_port: int
    imap_ssl_host: str
    smtp_ssl_port: int
    smtp_ssl_host: str


class Handler(ABC):
    @abstractmethod
    def set_prev(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, request) -> Optional[str]:
        pass

    @abstractmethod
    def execute(self, request)-> Any:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def set_prev(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any) -> Any:
        if self._next_handler is not None:
            response = self._next_handler.handle(request)
            if response:
                return self.execute(response)
        else:
            return self.execute(request)


class ImapHandler(AbstractHandler):
    def execute(self, request):
        email_object = EmailData(user_name=request["user_name"],
                                 password=request["password"],
                                 imap_ssl_port=request["imap_ssl_port"],
                                 imap_ssl_host=request["imap_ssl_host"],
                                 smtp_ssl_port=request["smtp_ssl_port"],
                                 smtp_ssl_host=request["smtp_ssl_host"])
        return email_object

    def handle(self, request: Any):
        return super().handle(request)


class AuthenticationHandler(AbstractHandler):
    def execute(self, request):
        imap_server = imaplib.IMAP4_SSL(request.imap_ssl_host, request.imap_ssl_port)
        imap_server.login(request.user_name, request.password)
        smtp_server = smtplib.SMTP_SSL(request.smtp_ssl_host, request.smtp_ssl_port)
        smtp_server.login(request.user_name, request.password)
        return imap_server, smtp_server

    def handle(self, request: Any):
        return super().handle(request)


class GetMessageHandler(AbstractHandler):
    def execute(self, request):
        imap_server, smtp_server = request
        self.__select_mail_box(imap_server)
        tmp, data = self.__search_mail_box(imap_server=imap_server, criterion='ALL')
        for num in data[0].split():
            tmp, data = self.__fetch_message(imap_server, num)
            message = self.__decode_message(data)
            email_message = email.message_from_string(message)
            headers = self.__get_header(email_message)
            # print(headers)
            self.__print_header(headers)
        self.__close_imap_server(imap_server)

    def __close_imap_server(self, imap_server):
        imap_server.close()

    def __print_header(self, headers):
        for h in headers.items():
            print(h)

    def __get_header(self, email_message):
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(email_message.as_string())
        return headers

    def __decode_message(self, data):
        message = data[0][1].decode('utf-8')
        return message

    def __fetch_message(self, imap_server, num):
        tmp, data = imap_server.fetch(num, '(RFC822)')
        return tmp, data

    def __search_mail_box(self, imap_server, criterion, char_set=None):
        tmp, data = imap_server.search(char_set, criterion)
        return tmp, data

    def __select_mail_box(self, imap_server):
        imap_server.select('INBOX')

    def handle(self, request: Any):
        return super().handle(request)


def client_code(handler: Handler, request) -> None:
    return handler.handle(request)


if __name__ == "__main__":
    imap = ImapHandler()
    auth = AuthenticationHandler()
    msg = GetMessageHandler()

    msg.set_prev(auth).set_prev(imap)
    request = {
        "user_name": "roboket.test@gmail.com",
        "password": "DDFlkjlkj.78908$%",
        "imap_ssl_port": 993,
        "imap_ssl_host": "imap.gmail.com",
        "smtp_ssl_port": 465,
        "smtp_ssl_host": "smtp.gmail.com",
    }
    # The client should be able to send a request to any handler, not just the
    # first one in the chain.
    print("Chain: Monkey > Squirrel > Dog")
    print(client_code(msg, request))

# class AuthenticationHandler(AbstractHandler):
#
#     def handle(self, request: Any) -> str:
#         response = super().handle(request)
#         if response is None:
#             return self.execute(request)
#
#     def execute(self, request):
#         self.__server = imaplib.IMAP4_SSL(self.__imap_ssl_host, self.__imap_ssl_port)
#         self.__server.login(self.__user_name, self.__password)
#         return __server

# class ImapHandler(object):
#     def __init__(self, email_information: EmailData):
#         self.__user_name, self.__password = email_information.user_name, email_information.password
#         self.__imap_ssl_port, self.__imap_ssl_host = email_information.imap_ssl_port, email_information.imap_ssl_host
#         self.__smtp_ssl_port, self.__smtp_ssl_host = email_information.smtp_ssl_port, email_information.smtp_ssl_host
#         self.__next_handler = self.__authenticate_imap

# def __authenticate_imap(self):
#     self.__server = imaplib.IMAP4_SSL(self.__imap_ssl_host, self.__imap_ssl_port)
#     self.__server.login(self.__user_name, self.__password)
#     return __server

# def __get_threaded_message(self):
