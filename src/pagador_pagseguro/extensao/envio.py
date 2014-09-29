# -*- coding: utf-8 -*-
from pagador.envio.serializacao import EntidadeSerializavel, Atributo


class Preferencia(EntidadeSerializavel):
    _atributos = ["notification_url", "external_reference", "expires", "expiration_date_from", "auto_return", "sponsor_id",
                  "expiration_date_to", "additional_info", "marketplace_fee", "items", "payer", "back_urls", "shipments"]
    atributos = [
        Atributo(atributo, eh_serializavel=(atributo == "payer" or atributo == "shipments" or atributo == "back_urls"), eh_lista=(atributo == "items"))
        for atributo in _atributos
    ]


class Item(EntidadeSerializavel):
    atributos = [
        Atributo("id"), Atributo("title"), Atributo("currency"), Atributo("picture_url"), Atributo("description"),
        Atributo("category_id"), Atributo("quantity"), Atributo("unit_price")
    ]


class Payer(EntidadeSerializavel):
    atributos = [
        Atributo("name"), Atributo("surname"), Atributo("email"), Atributo("date_created"),
        Atributo("address", eh_serializavel=True),
        Atributo("phone", eh_serializavel=True),
        Atributo("identification", eh_serializavel=True),
    ]


class Phone(EntidadeSerializavel):
    atributos = [Atributo("area_code"), Atributo("number")]


class Identification(EntidadeSerializavel):
    atributos = [Atributo("type"), Atributo("number")]


class PayerAddress(EntidadeSerializavel):
    atributos = [Atributo("street_name"), Atributo("street_number"), Atributo("zip_code")]


class BackUrls(EntidadeSerializavel):
    atributos = [Atributo("success"), Atributo("pending"), Atributo("failure")]


class Shipments(EntidadeSerializavel):
    atributos = [Atributo("receiver_address", eh_serializavel=True)]


class ReceiverAddress(EntidadeSerializavel):
    atributos = [Atributo("street_name"), Atributo("street_number"), Atributo("zip_code"), Atributo("floor"), Atributo("apartment")]


