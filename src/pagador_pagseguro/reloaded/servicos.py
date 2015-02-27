# -*- coding: utf-8 -*-
from urllib import urlencode
from li_common.comunicacao import requisicao
from pagador import settings
from pagador.reloaded import servicos


class InstalaMeioDePagamento(servicos.InstalaMeioDePagamento):
    campos = ['codigo_autorizacao', 'aplicacao']

    def __init__(self, loja_id, dados):
        super(InstalaMeioDePagamento, self).__init__(loja_id, dados)
        self.usa_alt = 'ua' in self.dados
        self.aplicacao = 'pagseguro-alternativo' if self.usa_alt else 'pagseguro'
        parametros = self.cria_entidade_de_pagador('ParametrosDeContrato', loja_id=loja_id).obter_para(self.aplicacao)
        self.app_key = parametros['app_secret']
        self.app_id = parametros['app_id']
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.xml, formato_resposta=requisicao.Formato.xml)

    @property
    def sandbox(self):
        return 'sandbox.' if (settings.ENVIRONMENT == 'local' or settings.ENVIRONMENT == 'development') else ''

    def montar_url_autorizacao(self):
        try:
            parametros_redirect = {'next_url': self.dados['next_url'], 'fase_atual': '2'}
        except KeyError:
            raise self.InstalacaoNaoFinalizada(u'Você precisa informar a url de redirecionamento na volta do PagSeguro na chave next_url do parâmetro dados.')
        dados = {
            'authorizationRequest': {
                'reference': self.loja_id,
                'permissions': [
                    {'code': 'CREATE_CHECKOUTS'},
                    {'code': 'SEARCH_TRANSACTIONS'},
                    {'code': 'RECEIVE_TRANSACTION_NOTIFICATIONS'},
                ],
                'redirectURL': '<![CDATA[{}?{}]]>'.format(settings.PAGSEGURO_REDIRECT_URL.format(self.loja_id), urlencode(parametros_redirect)),
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
            raise self.InstalacaoNaoFinalizada(u'Erro ao entrar em contato com o PagSeguro. Código: {} - Resposta: {}'.format(resposta.status_code, resposta.conteudo))
        code = resposta.conteudo['authorizationRequest']['code']
        return 'https://{}pagseguro.uol.com.br/v2/authorization/request.jhtml?code={}'.format(self.sandbox, code)

    def obter_dados(self):
        if 'notificationCode' not in self.dados:
            raise self.InstalacaoNaoFinalizada(u'O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo.')
        dados = {
            'appKey': self.app_key,
            'appId': self.app_id,
        }
        notification_code = self.dados['notificationCode']
        url = 'https://ws.{}pagseguro.uol.com.br/v2/authorizations/notifications/{}/?{}'.format(self.sandbox, notification_code, urlencode(dados))
        resposta = self.conexao.get(url)
        if resposta.sucesso:
            return {
                'codigo_autorizacao': resposta.conteudo['authorization']['code'],
                'aplicacao': self.aplicacao
            }
        raise self.InstalacaoNaoFinalizada(u'Erro ao entrar em contato com o PagSeguro. Código: {} - Resposta: {}'.format(resposta.status_code, resposta.conteudo))

    def desinstalar(self, dados):
        return {"redirect": "https://{}pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml".format(self.sandbox)}