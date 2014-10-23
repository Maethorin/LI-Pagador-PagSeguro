# -*- coding: utf-8 -*-
from pagador import settings
from pagador.acesso.externo import FormatoDeEnvio, TipoMetodo
from pagador.retorno.models import SituacaoPedido
from pagador.retorno.registro import RegistroBase
from pagador_pagseguro.extensao.seguranca import ParametrosPagSeguro


class SituacoesDePagamento(object):
    aguardando = "1"
    em_analise = "2"
    paga = "3"
    em_disputa = "5"
    devolvido = "6"
    cancelado = "7"
    charged_back = "8"

    @classmethod
    def do_tipo(cls, tipo):
        return getattr(cls, tipo, None)


class Registro(RegistroBase):
    def __init__(self, dados, tipo="retorno", configuracao=None):
        super(Registro, self).__init__(dados, configuracao)
        self.exige_autenticacao = True
        self.processa_resposta = True
        self.tipo = tipo
        self.formato_de_envio = FormatoDeEnvio.querystring
        self.metodo_request = TipoMetodo.get

    @property
    def url(self):
        end_point = "" if "transacao" in self.dados else "/notifications"
        return "https://ws.{}pagseguro.uol.com.br/v3/transactions{}/{}".format(self.sandbox, end_point, self.identificador_id)

    @property
    def pedido_numero(self):
        if self.retorno_de_requisicao:
            return self.dados["referencia"]
        return self.dados["transaction"]["reference"]

    @property
    def identificador_id(self):
        if self.retorno_de_requisicao:
            return self.dados["transacao"]
        if "notificationCode" in self.dados:
            return self.dados["notificationCode"]
        return None

    @property
    def valores_de_pagamento(self):
        if not "transaction" in self.dados:
            return {}
        valores = {
            "identificador_id": self.identificador_id,
        }
        if "code" in self.dados["transaction"]:
            valores["transacao_id"] = self.dados["transaction"]["code"]
        if "grossAmount" in self.dados["transaction"]:
            valores["valor_pago"] = self.dados["transaction"]["grossAmount"]
        return valores

    @property
    def deve_gravar_dados_de_pagamento(self):
        return self.obter_dados_do_gateway

    def __getattr__(self, name):
        if name.startswith("situacao_"):
            tipo = name.replace("situacao_", "")
            if not self.obter_dados_do_gateway:
                return tipo == "aguardando"
            return self.dados["transaction"]["status"] == SituacoesDePagamento.do_tipo(tipo)
        return object.__getattribute__(self, name)

    @property
    def situacao_do_pedido(self):
        if self.situacao_aguardando:
            return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO
        if self.situacao_em_analise:
            return SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE
        if self.situacao_paga:
            return SituacaoPedido.SITUACAO_PEDIDO_PAGO
        if self.situacao_em_disputa:
            return SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA
        if self.situacao_devolvido:
            return SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO
        if self.situacao_cancelado:
            return SituacaoPedido.SITUACAO_PEDIDO_CANCELADO
        if self.situacao_charged_back:
            return SituacaoPedido.SITUACAO_PAGTO_CHARGEBACK
        return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO

    @property
    def alterar_situacao(self):
        return self.obter_dados_do_gateway

    @property
    def retorno_de_requisicao(self):
        return self.tipo == "success"

    @property
    def retorno_de_notificacao(self):
        return self.tipo == "retorno"

    @property
    def obter_dados_do_gateway(self):
        return "transacao" in self.dados or "notificationCode" in self.dados

    @property
    def redireciona_para(self):
        if "next_url" in self.dados:
            tipo = self.tipo
            if self.situacao_aguardando or self.situacao_em_analise:
                tipo = 'pending'
            if self.situacao_cancelado:
                tipo = 'failure'
            return "{}?{}=1".format(self.dados["next_url"], tipo)
        return None

    def processar_resposta(self, resposta):
        retorno = self.formatador.xml_para_dict(resposta.content)
        return {"content": retorno, "status": resposta.status_code, "reenviar": False}

    @property
    def sandbox(self):
        return "sandbox." if (settings.ENVIRONMENT == "local" or settings.ENVIRONMENT == "development") else ""

    def gerar_dados_de_envio(self):
        usa_alt = self.configuracao.aplicacao == 'pagseguro-alternativo'
        parametros = ParametrosPagSeguro(self.dados["conta_id"], usa_alt)
        return {
            "appKey": parametros.app_secret,
            "appId": parametros.app_id,
        }
