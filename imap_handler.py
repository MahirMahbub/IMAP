from __future__ import annotations

import email
import imaplib
import smtplib
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, Dict

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
    def handle(self, request_data) -> Optional[str]:
        pass

    @abstractmethod
    def execute(self, request_data) -> Any:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def set_prev(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request_data: Any) -> Any:
        if self._next_handler is not None:
            response = self._next_handler.handle(request_data)
            if response:
                return self.execute(response)
        else:
            return self.execute(request_data)


class ImapHandler(AbstractHandler):
    def execute(self, request_data) -> EmailData:
        email_object: EmailData = EmailData(user_name=request_data["user_name"],
                                            password=request_data["password"],
                                            imap_ssl_port=request_data["imap_ssl_port"],
                                            imap_ssl_host=request_data["imap_ssl_host"],
                                            smtp_ssl_port=request_data["smtp_ssl_port"],
                                            smtp_ssl_host=request_data["smtp_ssl_host"])
        return email_object

    def handle(self, request_data: Any):
        return super().handle(request_data)


class AuthenticationHandler(AbstractHandler):
    def execute(self, request_data: EmailData) -> Tuple[imaplib.IMAP4_SSL, smtplib.SMTP_SSL]:
        imap_server: imaplib.IMAP4_SSL = imaplib.IMAP4_SSL(request_data.imap_ssl_host, request_data.imap_ssl_port)
        imap_server.login(request_data.user_name, request_data.password)
        smtp_server: smtplib.SMTP_SSL = smtplib.SMTP_SSL(request_data.smtp_ssl_host, request_data.smtp_ssl_port)
        smtp_server.login(request_data.user_name, request_data.password)
        return imap_server, smtp_server

    def handle(self, request_data: Any) -> Any:
        return super().handle(request_data)


class GetMessageHandler(AbstractHandler):
    def execute(self, request_data: Tuple[imaplib.IMAP4_SSL, smtplib.SMTP_SSL]) -> None:
        imap_server, smtp_server = request_data
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

    @staticmethod
    def __close_imap_server(imap_server) -> None:
        imap_server.close()

    @staticmethod
    def __print_header(headers) -> None:
        for h in headers.items():
            print(h)

    @staticmethod
    def __get_header(email_message) -> Dict[Any]:
        parser = email.parser.HeaderParser()
        headers = parser.parsestr(email_message.as_string())
        return headers

    @staticmethod
    def __decode_message(data) -> str:
        message = data[0][1].decode('utf-8')
        return message

    @staticmethod
    def __fetch_message(imap_server, num) -> Tuple[Any, Any]:
        tmp, data = imap_server.fetch(num, '(RFC822)')
        return tmp, data

    @staticmethod
    def __search_mail_box(imap_server, criterion, char_set=None) -> Tuple[Any, Any]:
        tmp, data = imap_server.search(char_set, criterion)
        return tmp, data

    @staticmethod
    def __select_mail_box(imap_server) -> None:
        imap_server.select('INBOX')

    def handle(self, request_data: Any) -> Any:
        return super().handle(request_data)


def main(handler: Handler, request_data) -> Any:
    return handler.handle(request_data)


if __name__ == "__main__":
    imap = ImapHandler()
    auth = AuthenticationHandler()
    msg = GetMessageHandler()

    msg.set_prev(auth).set_prev(imap)
    request_data_ = {
        "user_name": "roboket.test@gmail.com",
        "password": "DDFlkjlkj.78908$%",
        "imap_ssl_port": 993,
        "imap_ssl_host": "imap.gmail.com",
        "smtp_ssl_port": 465,
        "smtp_ssl_host": "smtp.gmail.com",
    }

    print(main(msg, request_data_))
