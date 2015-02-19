# -*- coding: utf-8 -*-
from urllib import urlencode
from li_common.comunicacao import requisicao
from pagador import settings

from pagador.reloaded import entidades
from pagador_pagseguro.reloaded import cadastro


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    _campos = ['ativo', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
    _codigo_gateway = 1

    def __init__(self, loja_id, codigo_pagamento=None):
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento)
        self.preencher_do_gateway(self._codigo_gateway, self._campos)
        self.formulario = cadastro.FormularioPagSeguro()
        self.eh_aplicacao = True


class InstaladorMeioDePagamento(entidades.InstaladorMeioDePagamento):
    def __init__(self, loja_id, dados):
        super(InstaladorMeioDePagamento, self).__init__(loja_id, dados)
        self.usa_alt = 'ua' in self.dados
        self.aplicacao = 'pagseguro-alternativo' if self.usa_alt else 'pagseguro'
        parametros = entidades.ParametrosDeContrato(loja_id).obter_para(self.aplicacao)
        self.app_key = parametros['app_secret']
        self.app_id = parametros['app_id']
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.xml, formato_resposta=requisicao.Formato.xml)
        self.parametros_redirect = {'next_url': dados['next_url']}

    @property
    def sandbox(self):
        return "sandbox." if (settings.ENVIRONMENT == "local" or settings.ENVIRONMENT == "development") else ""

    def montar_url_autorizacao(self):
        dados = {
            "authorizationRequest": {
                'reference': self.loja_id,
                'permissions': [
                    {"code": "CREATE_CHECKOUTS"},
                    {"code": "SEARCH_TRANSACTIONS"},
                    {"code": "RECEIVE_TRANSACTION_NOTIFICATIONS"},
                ],
                'redirectURL': "<![CDATA[{}?{}]]>".format(settings.PAGSEGURO_REDIRECT_URL.format(self.loja_id), urlencode(self.parametros_redirect)),
            }
        }
        dados_autorizacao = {
            'appKey': self.app_key,
            'appId': self.app_id,
        }
        url_autorizacao = 'https://ws.{}pagseguro.uol.com.br/v2/authorizations/request?{}'.format(self.sandbox, urlencode(dados_autorizacao))
        dados = self.formatador.dict_para_xml(dados)
        resposta = self.conexao.post(url_autorizacao, dados=dados)
        if not resposta.sucesso:
            raise self.InstalacaoNaoFinalizada(u"Erro ao entrar em contato com o PagSeguro. Código: {} - Resposta: {}".format(resposta.status_code, resposta.conteudo))
        code = resposta.conteudo["authorizationRequest"]["code"]
        return "https://{}pagseguro.uol.com.br/v2/authorization/request.jhtml?code={}".format(self.sandbox, code)

    def obter_dados(self):
        if not "notificationCode" not in self.dados:
            return {"erro": u"O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo."}
        dados = {
            'appKey': self.app_key,
            'appId': self.app_id,
        }
        notification_code = self.dados["notificationCode"]
        url = "https://ws.{}pagseguro.uol.com.br/v2/authorizations/notifications/{}/?{}".format(self.sandbox, notification_code, urlencode(dados))
        resposta = self.conexao.get(url)
        if resposta.sucesso:
            return {
                "codigo_autorizacao": resposta.conteudo["authorization"]["code"],
                "aplicacao": self.aplicacao
            }
        raise self.InstalacaoNaoFinalizada()
