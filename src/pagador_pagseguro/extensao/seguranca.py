# -*- coding: utf-8 -*-
from urllib import urlencode
from xml.etree import ElementTree

import requests

from pagador import settings
from pagador.seguranca import autenticador
from pagador.seguranca.autenticador import TipoAutenticacao
from pagador.seguranca.instalacao import Parametros, InstalacaoNaoFinalizada
from pagador.settings import PAGSEGURO_REDIRECT_URL


class ParametrosPagSeguro(Parametros):
    @property
    def chaves(self):
        return ["app_secret", "app_id"]


class Credenciador(autenticador.Credenciador):
    def __init__(self, configuracao):
        self.conta_id = configuracao.conta_id
        self.configuracao = configuracao
        self.codigo_autorizacao = getattr(configuracao, "codigo_autorizacao", "")
        self.tipo = TipoAutenticacao.query_string

    def _atualiza_credenciais(self):
        self.codigo_autorizacao = getattr(self.configuracao, "codigo_autorizacao", "")

    def obter_credenciais(self):
        self._atualiza_credenciais()
        return self.codigo_autorizacao

    def esta_valido(self):
        if not self.codigo_autorizacao:
            return False
        return True


class Instalador(object):
    campos = ["codigo_autorizacao"]

    def __init__(self, **filtro_parametros):
        self.conta_id = filtro_parametros["id"]
        self.parametros = ParametrosPagSeguro("pagseguro", **filtro_parametros)

    @property
    def sandbox(self):
        return "sandbox." if settings.DEBUG else ""

    def url_ativador(self, parametros_redirect):
        dados = {
            'reference': self.conta_id,
            'permissions': "CREATE_CHECKOUTS,RECEIVE_TRANSACTION_NOTIFICATIONS,SEARCH_TRANSACTIONS",
            'redirectURL': "{}?{}".format(PAGSEGURO_REDIRECT_URL.format(self.conta_id), urlencode(parametros_redirect)),
            'appKey': self.parametros.app_secret,
            'appId': self.parametros.app_id,
        }
        print dados
        url_autorizacao = 'https://ws.{}pagseguro.uol.com.br/v2/authorizations/request/'.format(self.sandbox)
        reponse_code = requests.post(url_autorizacao, data=dados)
        if reponse_code.status_code != 200:
            raise InstalacaoNaoFinalizada(u"erro na geração da url. Code: {} - Resposta: {}".format(reponse_code.status_code, reponse_code.content))
        code = self.parse_resposta(reponse_code.content)["code"]
        return "https://{}pagseguro.uol.com.br/v2/authorization/request.jhtml?code={}".format(self.sandbox, code)

    def obter_dados(self, dados):
        if not "notificationCode" in dados:
            return {"erro": u"O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo."}
        dados.update({
            'appKey': self.parametros.app_secret,
            'appId': self.parametros.app_id,
        })
        notification_code = dados["notificationCode"]
        del dados["notificationCode"]
        url = "https://ws.pagseguro.uol.com.br/v2/authorizations/notifications/{}/?{}".format(notification_code, urlencode(dados))
        resposta = requests.get(url)
        if resposta.status_code == 200:
            return self.parse_resposta(resposta.content)
        return {"erro": resposta.content}

    def dados_de_instalacao(self, dados):
        dados_instalacao = self.obter_dados(dados)
        if "erro" in dados_instalacao:
            raise InstalacaoNaoFinalizada(dados_instalacao["erro"])
        return {
            "codigo_autorizacao": dados_instalacao["code"]
        }

    def desinstalar(self, dados):
        return {"redirect": "https://pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml"}

    def parse_resposta(self, content):
        root = ElementTree.fromstring(content)
        resultado = {}
        for child in root:
            resultado[child.tag] = child.text
        return resultado
