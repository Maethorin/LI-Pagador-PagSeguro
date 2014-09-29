# -*- coding: utf-8 -*-
import json
from pagador.retorno.models import SituacaoPedido
from pagador.retorno.registro import RegistroBase


class SituacoesDePagamento(object):
    aprovado = "approved"
    pendente = "pending"
    em_andamento = "in_process"
    rejeitado = "rejected"
    devolvido = "refunded"
    cancelado = "cancelled"
    em_mediacao = "in_mediation"
    charged_back = "charged_back"

    @classmethod
    def do_tipo(cls, tipo):
        return getattr(cls, tipo, None)


class Registro(RegistroBase):
    def __init__(self, dados, tipo="retorno"):
        super(Registro, self).__init__(dados)
        self.exige_autenticacao = True
        self.processa_resposta = True
        self.tipo = tipo
        self.envio_por_querystring = False

    @property
    def url(self):
        return "https://api.mercadolibre.com/collections/notifications/{}".format(self.dados["id"])

    @property
    def pedido_numero(self):
        if self.retorno_de_notificacao:
            return self.dados["collection"]["external_reference"]
        return self.dados["external_reference"]

    @property
    def identificador_id(self):
        if self.retorno_de_preferencia:
            return self.dados["preference_id"]
        return None

    def __getattr__(self, name):
        if name.startswith("situacao_"):
            tipo = name.replace("situacao_", "")
            if self.retorno_de_preferencia:
                if tipo != "aprovado" and tipo != "pendente":
                    return False
                if self.dados["collection_status"] is None:
                    return False
                return self.dados["collection_status"] == SituacoesDePagamento.do_tipo(tipo)
            if self.retorno_de_notificacao:
                return self.dados["collection"]["status"] == SituacoesDePagamento.do_tipo(tipo)
        return object.__getattribute__(self, name)

    @property
    def situacao_do_pedido(self):
        if self.situacao_aprovado:
            return SituacaoPedido.SITUACAO_PEDIDO_PAGO
        if self.situacao_em_andamento or self.situacao_pendente:
            return SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE
        if self.situacao_rejeitado:
            return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO
        if self.situacao_devolvido:
            return SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO
        if self.situacao_cancelado:
            return SituacaoPedido.SITUACAO_PEDIDO_CANCELADO
        if self.situacao_em_mediacao:
            return SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA
        if self.situacao_charged_back:
            return SituacaoPedido.SITUACAO_PAGTO_CHARGEBACK
        return SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO

    @property
    def alterar_situacao(self):
        return True

    @property
    def retorno_de_preferencia(self):
        return "collection_status" in self.dados

    @property
    def retorno_de_notificacao(self):
        return "collection" in self.dados

    @property
    def obter_dados_do_gateway(self):
        return "topic" in self.dados and self.dados["topic"] == "payment"

    @property
    def redireciona_para(self):
        if "next_url" in self.dados:
            return "{}?{}=1".format(self.dados["next_url"], self.tipo)
        return None

    def processar_resposta(self, resposta):
        retorno = json.loads(resposta.content)
        if resposta.status_code == 401:
            reenviar = retorno["message"] == "expired_token"
            return {"content": retorno["message"], "status": 401 if reenviar else 400, "reenviar": reenviar}
        if resposta.status_code == 400:
            reenviar = retorno["error"] == "invalid_access_token"
            return {"content": retorno["message"], "status": 401 if reenviar else 400, "reenviar": reenviar}
        return {"content": retorno, "status": resposta.status_code, "reenviar": False}

