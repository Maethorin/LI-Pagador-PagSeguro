# -*- coding: utf-8 -*-
from urllib import urlencode
from xml.etree import ElementTree

import requests

from pagador import settings
from pagador.seguranca import autenticador
from pagador.seguranca.autenticador import TipoAutenticacao
from pagador.seguranca.instalacao import Parametros, InstalacaoNaoFinalizada, InstaladorBase
from pagador.settings import PAGSEGURO_REDIRECT_URL


class ParametrosPagSeguro(Parametros):
    def __init__(self, conta_id, usa_alt=False):
        meio_pagamento = 'pagseguro'
        if usa_alt:
            meio_pagamento = 'pagseguro-alternativo'
        super(ParametrosPagSeguro, self).__init__(meio_pagamento, id=conta_id)

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

    @property
    def chave(self):
        return "authorizationCode"

    def obter_credenciais(self):
        self._atualiza_credenciais()
        return self.codigo_autorizacao

    def esta_valido(self):
        if not self.codigo_autorizacao:
            return False
        return True


class Instalador(InstaladorBase):
    campos = ["codigo_autorizacao", "aplicacao"]

    def __init__(self, configuracao, **filtro_parametros):
        super(Instalador, self).__init__(configuracao)
        self.conta_id = filtro_parametros["id"]
        self._parametros = None
        self.usa_alt = False

    @property
    def parametros(self):
        if not self._parametros:
            self._parametros = ParametrosPagSeguro(conta_id=self.conta_id, usa_alt=self.usa_alt)
        return self._parametros

    @property
    def sandbox(self):
        return "sandbox." if (settings.ENVIRONMENT == "local" or settings.ENVIRONMENT == "development") else ""

    def url_ativador(self, parametros_redirect):
        self._parametros = None
        self.usa_alt = 'ua' in parametros_redirect
        dados = {
            "authorizationRequest": {
                'reference': self.conta_id,
                'permissions': [
                    {"code": "CREATE_CHECKOUTS"},
                    {"code": "SEARCH_TRANSACTIONS"},
                    {"code": "RECEIVE_TRANSACTION_NOTIFICATIONS"},
                ],
                'redirectURL': "<![CDATA[{}?{}]]>".format(PAGSEGURO_REDIRECT_URL.format(self.conta_id), urlencode(parametros_redirect)),
            }
        }
        dados_autorizacao = {
            'appKey': self.parametros.app_secret,
            'appId': self.parametros.app_id,
        }
        url_autorizacao = 'https://ws.{}pagseguro.uol.com.br/v2/authorizations/request?{}'.format(self.sandbox, urlencode(dados_autorizacao))
        dados = self.formatador.dict_para_xml(dados)
        reponse_code = requests.post(url_autorizacao, data=dados, headers={"Content-Type": "application/xml; charset=ISO-8859-1"})
        if reponse_code.status_code != 200:
            raise InstalacaoNaoFinalizada(u"Erro ao entrar em contato com o PagSeguro. Código: {} - Resposta: {}".format(reponse_code.status_code, reponse_code.content))
        code = self.formatador.xml_para_dict(reponse_code.content)["authorizationRequest"]["code"]
        return "https://{}pagseguro.uol.com.br/v2/authorization/request.jhtml?code={}".format(self.sandbox, code)

    def obter_dados(self, dados):
        if not "notificationCode" in dados:
            return {"erro": u"O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo."}
        self.usa_alt = 'ua' in dados
        self._parametros = None
        if self.usa_alt:
            del dados["ua"]
        dados.update({
            'appKey': self.parametros.app_secret,
            'appId': self.parametros.app_id,
        })
        notification_code = dados["notificationCode"]
        del dados["notificationCode"]
        url = "https://ws.{}pagseguro.uol.com.br/v2/authorizations/notifications/{}/?{}".format(self.sandbox, notification_code, urlencode(dados))
        resposta = requests.get(url)
        if resposta.status_code == 200:
            return self.formatador.xml_para_dict(resposta.content)
        return {"xerro": resposta.content}

    def dados_de_instalacao(self, dados):
        dados_instalacao = self.obter_dados(dados)
        if "erro" in dados_instalacao:
            raise InstalacaoNaoFinalizada(dados_instalacao["erro"])
        return {
            "codigo_autorizacao": dados_instalacao["authorization"]["code"],
            "aplicacao": ("pagseguro-alternativo" if self.usa_alt else "pagseguro")
        }

    def desinstalar(self, dados):
        return {"redirect": "https://{}pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml".format(self.sandbox)}
