# -*- coding: utf-8 -*-
from pagador.envio.serializacao import EntidadeSerializavel, Atributo


class Checkout(EntidadeSerializavel):
    atributos = [
        Atributo("appId"), Atributo("appKey"), Atributo("currency"), Atributo("reference"), Atributo("senderName"), Atributo("senderAreaCode"),  Atributo("senderPhone"),
        Atributo("senderEmail"), Atributo("shippingType"), Atributo("shippingAddressStreet"), Atributo("shippingAddressNumber"), Atributo("shippingAddressComplement"),
        Atributo("shippingAddressDistrict"), Atributo("shippingAdressPostalCode"), Atributo("shippingAdressCity"), Atributo("shippingAdressState"), Atributo("shippingAdressCountry"),
        Atributo("shippingCost"), , Atributo("extraAmount"), Atributo("redirectURL"), Atributo("notificationURL")
    ]

    @classmethod
    def cria_item(cls, item):
        cls.atributos.append(Atributo("itemId{}".format(item)))
        cls.atributos.append(Atributo("itemDescription{}".format(item)))
        cls.atributos.append(Atributo("itemAmount{}".format(item)))
        cls.atributos.append(Atributo("itemQuantity{}".format(item)))
