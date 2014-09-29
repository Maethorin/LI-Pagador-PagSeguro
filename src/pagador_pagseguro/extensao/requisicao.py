# -*- coding: utf-8 -*-
import json
from pagador.envio.requisicao import Enviar
from pagador.envio.serializacao import Atributo
from pagador.retorno.models import SituacaoPedido
from pagador.settings import MERCADOPAGO_PREFERENCE_NOTIFICATION_URL, MEDIA_URL

from pagador_pagseguro.extensao.envio import Preferencia, Payer, BackUrls, Shipments, Item, Phone, Identification, PayerAddress, ReceiverAddress
from pagador_pagseguro.extensao.seguranca import ParametrosMercadoPago


class EnviarPedido(Enviar):
    def __init__(self, pedido, dados, configuracao_pagamento):
        super(EnviarPedido, self).__init__(pedido, dados, configuracao_pagamento)
        self.exige_autenticacao = True
        self.processa_resposta = True
        self.url = "https://api.mercadolibre.com/checkout/preferences"
        self.grava_identificador = True
        self.envio_por_querystring = False

    def gerar_dados_de_envio(self):
        notification_url = MERCADOPAGO_PREFERENCE_NOTIFICATION_URL.format(self.pedido.conta.id)
        preferencia = Preferencia(
            auto_return="approved",
            notification_url=notification_url,
            external_reference=self.pedido.numero,
            payer=Payer(
                name=self.pedido.cliente.nome.split()[0],
                surname=self.pedido.cliente.nome.split()[-1],
                email=self.pedido.cliente.email,
                date_created=self.formatador.formata_data(self.pedido.cliente.data_criacao, iso=True),
                phone=self.telefone,
                identification=self.identificacao,
                address=PayerAddress(
                    street_name=self.pedido.cliente.endereco.endereco,
                    street_number=self.pedido.cliente.endereco.numero,
                    zip_code=self.pedido.cliente.endereco.cep,
                )
            ),
            back_urls=BackUrls(
                success="{}/success?next_url={}".format(notification_url, self.dados["next_url"]),
                pending="{}/pending?next_url={}".format(notification_url, self.dados["next_url"]),
                failure="{}/failure?next_url={}".format(notification_url, self.dados["next_url"])
            ),
            shipments=Shipments(
                receiver_address=ReceiverAddress(
                    street_name=self.pedido.endereco_entrega.endereco,
                    street_number=self.pedido.endereco_entrega.numero,
                    apartment=self.pedido.endereco_entrega.complemento,
                    zip_code=self.pedido.endereco_entrega.cep,
                )
            ),
            items=self.items
        )
        parametros = ParametrosMercadoPago("mercadopago", id=self.pedido.conta.id)
        try:
            sponsor_id = int(parametros.sponsor_id)
        except (AttributeError, ValueError):
            sponsor_id = None
        if sponsor_id:
            preferencia.define_valor_de_atributo(Atributo("sponsor_id"), {"sponsor_id": sponsor_id})
        return preferencia.to_dict()

    @property
    def identificacao(self):
        if self.pedido.cliente.endereco.tipo == "PF":
            return Identification(type="CPF", number=self.pedido.cliente.endereco.cpf)
        else:
            return Identification(type="CNPJ", number=self.pedido.cliente.endereco.cnpj)

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
            numero = self.formatador.converte_tel_em_tupla_com_ddd(telefone)
            return Phone(area_code=numero[0], number=numero[1])
        return ''

    @property
    def items(self):
        items = [
            Item(
                id=item.sku,
                title=item.nome,
                currency_id="BRL",
                unit_price=self.formatador.formata_decimal(item.preco_venda, como_float=True),
                quantity=self.formatador.formata_decimal(item.quantidade, como_float=True),
                category_id="others",
                picture_url=self.obter_url_da_imagem(item)
            )
            for item in self.pedido.itens.all()
        ]
        items.append(Item(title="Frete", quantity=1, currency_id="BRL", unit_price=self.formatador.formata_decimal(self.pedido.valor_envio, como_float=True)))
        return items

    def obter_situacao_do_pedido(self, status_requisicao):
        return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO

    def processar_resposta(self, resposta):
        retorno = json.loads(resposta.content)
        if resposta.status_code == 401:
            reenviar = retorno["message"] == "expired_token"
            return {"content": retorno["message"], "status": 401 if reenviar else 400, "reenviar": reenviar}
        if resposta.status_code == 400:
            reenviar = retorno["error"] == "invalid_access_token"
            return {"content": retorno["message"], "status": 401 if reenviar else 400, "reenviar": reenviar}
        if resposta.status_code in (201, 200):
            return {"content": {"url": retorno["init_point"]}, "status": 200, "reenviar": False, "identificador": retorno["id"]}
        return {"content": retorno, "status": resposta.status_code, "reenviar": False}

    def obter_url_da_imagem(self, item):
        if item.produto.cache_imagem_principal and item.produto.cache_imagem_principal.caminho:
            return "{}800x800/{}".format(MEDIA_URL, item.produto.cache_imagem_principal.caminho)
        return ""
