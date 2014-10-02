# -*- coding: utf-8 -*-
import json
from pagador import settings
from pagador.envio.requisicao import Enviar
from pagador.retorno.models import SituacaoPedido
from pagador.settings import PAGSEGURO_PREFERENCE_NOTIFICATION_URL

from pagador_pagseguro.extensao.envio import Checkout
from pagador_pagseguro.extensao.seguranca import ParametrosPagSeguro


class TipoEnvio(object):
    def __init__(self, codigo):
        self.codigo = codigo

    @property
    def valor(self):
        if self.codigo == "pac":
            return 1
        if "sedex" in self.codigo:
            return 2
        return 3


class EnviarPedido(Enviar):
    def __init__(self, pedido, dados, configuracao_pagamento):
        super(EnviarPedido, self).__init__(pedido, dados, configuracao_pagamento)
        self.exige_autenticacao = True
        self.processa_resposta = True
        self.url = "https://ws.{}pagseguro.uol.com.br/v2/checkout".format(self.sandbox)
        self.grava_identificador = False
        self.envio_por_querystring = True
        self.headers = {"Content-Type": "application/x-www-form-urlencoded; charset=ISO-8859-1"}
        for item in range(0, len(self.pedido.itens.all())):
            Checkout.cria_item(item)

    @property
    def sandbox(self):
        # return ""
        return "sandbox." if settings.DEBUG else ""

    @property
    def telefone(self):
        telefone = None
        if self.pedido.cliente.telefone_principal:
            telefone = self.pedido.cliente.telefone_principal
        elif self.pedido.cliente.telefone_comercial:
            telefone = self.pedido.cliente.telefone_comercial
        elif self.pedido.cliente.telefone_celular:
            telefone = self.pedido.cliente.telefone_celular
        if telefone:
            return self.formatador.converte_tel_em_tupla_com_ddd(telefone)
        return '', ''

    def gerar_dados_de_envio(self):
        notification_url = PAGSEGURO_PREFERENCE_NOTIFICATION_URL.format(self.pedido.conta.id)
        parametros = ParametrosPagSeguro(conta_id=self.pedido.conta.id, usa_alt=(self.configuracao_pagamento.aplicacao == 'pagseguro-alternativo'))
        numero_telefone = self.telefone
        envio = self.pedido.pedido_envio.envio
        checkout = Checkout(
            app_key=parametros.app_secret,
            app_id=parametros.app_id,
            currency="BRL",
            reference=self.pedido.numero,
            notification_url=notification_url,
            redirect_url="{}/success?next_url={}&referencia={}".format(notification_url, self.dados["next_url"], self.pedido.numero),

            sender_name=self.pedido.cliente.nome,
            sender_area_code=numero_telefone[0],
            sender_phone=numero_telefone[1],
            sender_email=self.formatador.trata_email_com_mais(self.pedido.cliente.email),

            shipping_type=TipoEnvio(envio.codigo).valor,
            shipping_cost=self.formatador.formata_decimal(self.pedido.valor_envio),
            shipping_address_street=self.pedido.endereco_entrega.endereco,
            shipping_address_number=self.pedido.endereco_entrega.numero,
            shipping_address_complement=self.pedido.endereco_entrega.complemento,
            shipping_address_district=self.pedido.endereco_entrega.bairro,
            shipping_address_postal_code=self.pedido.endereco_entrega.cep,
            shipping_address_city=self.pedido.endereco_entrega.cidade,
            shipping_address_state=self.pedido.endereco_entrega.estado,
            shipping_address_country="BRA"

        )
        for indice, item in enumerate(self.pedido.itens.all()):
            self.define_valor_de_atributo_de_item(checkout, "Id", indice, item.sku[:100])
            self.define_valor_de_atributo_de_item(checkout, "Description", indice, item.nome[:100])
            self.define_valor_de_atributo_de_item(checkout, "Amount", indice, self.formatador.formata_decimal(item.preco_venda))
            self.define_valor_de_atributo_de_item(checkout, "Quantity", indice, self.formatador.formata_decimal(item.quantidade, como_int=True))
        return checkout.to_dict()

    def define_valor_de_atributo_de_item(self, checkout, atributo, indice, valor):
        indice += 1
        nome = "item{}{}".format(atributo, indice)
        atributo = "item_{}{}".format(atributo, indice)
        checkout.define_valor_de_atributo(nome, {atributo.lower(): valor})

    def obter_situacao_do_pedido(self, status_requisicao):
        return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO

    def processar_resposta(self, resposta):
        if resposta.status_code == 401:
            return {"content": {"mensagem": u"Autorização da plataforma falhou em {}".format(self.url)}, "status": resposta.status_code, "reenviar": False}
        retorno = self.formatador.xml_para_dict(resposta.content)
        if resposta.status_code in (201, 200):
            url = "https://{}pagseguro.uol.com.br/v2/checkout/payment.html?code={}".format(self.sandbox, retorno["checkout"]["code"])
            return {"content": {"url": url}, "status": 200, "reenviar": False}
        mensagem = []
        if "errors" in retorno:
            if type(retorno["errors"]) is list:
                for erro in retorno["errors"]:
                    mensagem.append("{} - {}".format(erro["error"]["code"], erro["error"]["message"]))
            else:
                mensagem.append("{} - {}".format(retorno["errors"]["code"], retorno["errors"]["message"]))

        return {"content": {"mensagem": ", ".join(mensagem)}, "status": resposta.status_code, "reenviar": False}
