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
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=loja_id).obter_para(self.aplicacao)
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
        return {'redirect': 'https://{}pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'.format(self.sandbox)}


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.query_string
        self.codigo_autorizacao = str(getattr(self.configuracao, 'codigo_autorizacao', ''))
        self.chave = 'authorizationCode'

    def obter_credenciais(self):
        return self.codigo_autorizacao


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.form_urlencode, formato_resposta=requisicao.Formato.xml)
        self.resposta_pagseguro = None
        self.url = 'https://ws.{}pagseguro.uol.com.br/v2/checkout'.format(self.sandbox)

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def envia_pagamento(self, tentativa=1):
        self.resposta_pagseguro = self.conexao.post(self.url, self.malote.to_dict())

    def processa_dados_pagamento(self):
        self.resultado = self._processa_resposta()

    def _processa_resposta(self):
        status_code = self.resposta_pagseguro.status_code
        if self.resposta_pagseguro.erro_servidor:
            return {'mensagem': u'O servidor do PagSeguro está indisponível nesse momento.', 'status_code': status_code}
        if self.resposta_pagseguro.timeout:
            return {'mensagem': u'O servidor do PagSeguro não respondeu em tempo útil.', 'status_code': status_code}
        if self.resposta_pagseguro.nao_autenticado or self.resposta_pagseguro.nao_autorizado:
            return {'mensagem': u'Autenticação da loja com o PagSeguro Falhou. Contate o SAC da loja.', 'status_code': status_code}
        if self.resposta_pagseguro.sucesso:
            url = 'https://{}pagseguro.uol.com.br/v2/checkout/payment.html?code={}'.format(self.sandbox, self.resposta_pagseguro.conteudo['checkout']['code'])
            return {'url': url}
        if 'errors' in self.resposta_pagseguro.conteudo:
            erros = self.resposta_pagseguro.conteudo['errors']
            mensagens = []
            if type(erros) is list:
                for erro in erros:
                    mensagens.append('{} - {}'.format(erro['error']['code'], erro['error']['message']))
            else:
                mensagens.append('{} - {}'.format(erros['error']['code'], erros['error']['message']))
            raise self.EnvioNaoRealizado(u'Ocorreram erros no envio dos dados para o PagSeguro', self.loja_id, self.pedido.numero, dados_envio=self.malote.to_dict(), erros=mensagens)


class SituacoesDePagamento(object):
    """
    Traduz os códigos de status do PagSeguro em algo que o pagador entenda
    Ver status disponíveis em:
    https://pagseguro.uol.com.br/v2/guia-de-integracao/api-de-notificacoes.html
    """
    disponivel = '4'

    DE_PARA = {
        '1': servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO,
        '2': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        '3': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        '5': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA,
        '6': servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO,
        '7': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
        '8': servicos.SituacaoPedido.SITUACAO_PAGTO_CHARGEBACK
    }

    @classmethod
    def do_tipo(cls, tipo):
        return cls.DE_PARA.get(tipo, None)


class RegistraResultado(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraResultado, self).__init__(loja_id, dados)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring, formato_resposta=requisicao.Formato.xml)
        self.resposta_pagseguro = None
        self.redirect_para = dados.get('next_url', None)
        self.faz_http = True

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def monta_dados_pagamento(self):
        if self.resposta_pagseguro:
            self.dados_pagamento['identificador_id'] = self.dados['transacao']
            self.pedido_numero = self.dados["referencia"]
            transacao = self.resposta_pagseguro.conteudo['transaction']
            if 'code' in transacao:
                self.dados_pagamento['transacao_id'] = transacao['code']
            if 'grossAmount' in transacao:
                self.dados_pagamento['valor_pago'] = transacao['grossAmount']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(transacao['status'])
        self.resultado = {'resultado': 'OK'}

    def obtem_informacoes_pagamento(self):
        if self.deve_obter_informacoes_pagseguro:
            aplicacao = 'pagseguro_alternativo' if self.configuracao.aplicacao == 'pagseguro_alternativo' else 'pagseguro'
            parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
            dados = {
                'appKey': parametros['app_secret'],
                'appId': parametros['app_id'],
            }
            self.resposta_pagseguro = self.conexao.get(self.url, dados=dados)

    @property
    def deve_obter_informacoes_pagseguro(self):
        return 'transacao' in self.dados

    @property
    def url(self):
        return 'https://ws.{}pagseguro.uol.com.br/v3/transactions/{}'.format(self.sandbox, self.dados['transacao'])


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring, formato_resposta=requisicao.Formato.xml)
        self.resposta_pagseguro = None
        self.redirect_para = None
        self.faz_http = True

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def monta_dados_pagamento(self):
        if self.resposta_pagseguro:
            transacao = self.resposta_pagseguro.conteudo['transaction']
            self.pedido_numero = transacao["reference"]
            if 'code' in transacao:
                self.dados_pagamento['transacao_id'] = transacao['code']
            if 'grossAmount' in transacao:
                self.dados_pagamento['valor_pago'] = transacao['grossAmount']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(transacao['status'])
        self.resultado = {'resultado': 'OK'}

    def obtem_informacoes_pagamento(self):
        if self.deve_obter_informacoes_pagseguro:
            aplicacao = 'pagseguro_alternativo' if self.configuracao.aplicacao == 'pagseguro_alternativo' else 'pagseguro'
            parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
            dados = {
                'appKey': parametros['app_secret'],
                'appId': parametros['app_id'],
            }
            self.resposta_pagseguro = self.conexao.get(self.url, dados=dados)

    @property
    def deve_obter_informacoes_pagseguro(self):
        return 'notificationCode' in self.dados

    @property
    def url(self):
        return 'https://ws.{}pagseguro.uol.com.br/v3/transactions/notifications/{}'.format(self.sandbox, self.dados['notificationCode'])
