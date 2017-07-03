# -*- coding: utf-8 -*-

from flask_mail import Message
from app import app, mail
from .decorators import async


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    send_async_email(app, msg)
