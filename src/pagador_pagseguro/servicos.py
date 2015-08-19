# -*- coding: utf-8 -*-
import json
from urllib import urlencode

from li_common.comunicacao import requisicao

from pagador import settings, servicos


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
            if self.usa_alt:
                parametros_redirect['ua'] = 1
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
                'redirectURL': '<![CDATA[{}?{}]]>'.format(settings.INSTALAR_REDIRECT_URL.format(self.loja_id, 'pagseguro'), urlencode(parametros_redirect)),
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
        return {'url': 'https://{}pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'.format(self.sandbox)}


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.query_string
        self.codigo_autorizacao = str(getattr(self.configuracao, 'codigo_autorizacao', ''))
        self.chave = 'authorizationCode'

    def obter_credenciais(self):
        return self.codigo_autorizacao

MENSAGENS_ERRO = {
    '11033': u'Um ou mais produtos no carrinho está sem nome.',
    '11013': u'O CEP do comprador informado não parece ser válido'
}


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.form_urlencode, formato_resposta=requisicao.Formato.xml)
        self.resposta = None
        self.url = 'https://ws.{}pagseguro.uol.com.br/v2/checkout'.format(self.sandbox)

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def montar_malote(self):
        self.malote = self.cria_entidade_extensao('Malote', configuracao=self.configuracao)
        aplicacao = 'pagseguro-alternativo' if self.configuracao.aplicacao == 'pagseguro-alternativo' else 'pagseguro'
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
        self.malote.monta_conteudo(pedido=self.pedido, parametros_contrato=parametros, dados=self.dados)

    def envia_pagamento(self, tentativa=1):
        self.dados_enviados = self.malote.to_dict()
        self.resposta = self.conexao.post(self.url, self.dados_enviados)

    def processa_dados_pagamento(self):
        self.resultado = self._processa_resposta()

    def trata_mensagem_conhecida(self, erro, mensagens):
        code = str(erro['error']['code'])
        message = erro['error']['message']
        mensagem_conhecida = False
        if code in MENSAGENS_ERRO:
            message = MENSAGENS_ERRO['code']
            mensagem_conhecida = True
        mensagens.append(u'{} - {}'.format(code, message))
        return mensagem_conhecida

    def _processa_resposta(self):
        status_code = self.resposta.status_code
        if self.resposta.erro_servidor:
            return {'mensagem': u'O servidor do PagSeguro está indisponível nesse momento.', 'status_code': status_code}
        if self.resposta.timeout:
            return {'mensagem': u'O servidor do PagSeguro não respondeu em tempo útil.', 'status_code': status_code}
        if self.resposta.nao_autenticado or self.resposta.nao_autorizado:
            return {'mensagem': u'Autenticação da loja com o PagSeguro Falhou. Contate o SAC da loja.', 'status_code': status_code}
        if self.resposta.sucesso:
            url = 'https://{}pagseguro.uol.com.br/v2/checkout/payment.html?code={}'.format(self.sandbox, self.resposta.conteudo['checkout']['code'])
            return {'url': url}
        if 'errors' in self.resposta.conteudo:
            erros = self.resposta.conteudo['errors']
            sem_excecao = False
            mensagens = []
            if type(erros) is list:
                for erro in erros:
                    sem_excecao = self.trata_mensagem_conhecida(erro, mensagens)
            else:
                sem_excecao = self.trata_mensagem_conhecida(erros, mensagens)
            if sem_excecao:
                return {'mensagem': u'\n'.join(mensagens), 'status_code': status_code, 'fatal': True}
            raise self.EnvioNaoRealizado(u'Ocorreram erros no envio dos dados para o PagSeguro', self.loja_id, self.pedido.numero, dados_envio=self.malote.to_dict(), erros=mensagens)
        raise self.EnvioNaoRealizado(u'O PagSeguro não enviou uma resposta válida', self.loja_id, self.pedido.numero, dados_envio=self.malote.to_dict(), erros=[])


class SituacoesDePagamento(servicos.SituacoesDePagamento):
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


class RegistraResultado(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraResultado, self).__init__(loja_id, dados)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring, formato_resposta=requisicao.Formato.xml)
        self.redirect_para = dados.get('next_url', None)
        self.faz_http = True

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def monta_dados_pagamento(self):
        if self.deve_obter_informacoes_pagseguro and self.resposta.sucesso:
            self.dados_pagamento['identificador_id'] = self.dados['transacao']
            self.pedido_numero = self.dados["referencia"]
            transacao = self.resposta.conteudo['transaction']
            if 'code' in transacao:
                self.dados_pagamento['transacao_id'] = transacao['code']
            if 'grossAmount' in transacao:
                self.dados_pagamento['valor_pago'] = transacao['grossAmount']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(transacao['status'])
            self.resultado = 'sucesso'
        else:
            self.resultado = 'pendente'

    def _gera_dados_envio(self):
        aplicacao = 'pagseguro-alternativo' if self.configuracao.aplicacao == 'pagseguro-alternativo' else 'pagseguro'
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
        return {
            'appKey': parametros['app_secret'],
            'appId': parametros['app_id'],
        }

    def obtem_informacoes_pagamento(self):
        if self.deve_obter_informacoes_pagseguro:
            self.dados_enviados = self._gera_dados_envio()
            self.resposta = self.conexao.get(self.url, dados=self.dados_enviados)

    @property
    def deve_obter_informacoes_pagseguro(self):
        return 'transacao' in self.dados

    @property
    def url(self):
        if self.deve_obter_informacoes_pagseguro:
            return 'https://ws.{}pagseguro.uol.com.br/v3/transactions/{}'.format(self.sandbox, self.dados['transacao'])
        return ''


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring, formato_resposta=requisicao.Formato.xml)
        self.faz_http = True

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def _define_valor_e_situacao(self, transacao):
        if 'grossAmount' in transacao:
            self.dados_pagamento['valor_pago'] = transacao['grossAmount']
        self.situacao_pedido = SituacoesDePagamento.do_tipo(transacao['status'])

    def monta_dados_pagamento(self):
        if self.deve_obter_informacoes_pagseguro and self.resposta.sucesso:
            try:
                transacao = self.resposta.conteudo['transaction']
            except KeyError:
                raise self.RegistroDePagamentoInvalido(u'O PagSeguro não retornou os dados da transação. Os dados retornados foram: {}'.format(json.dumps(self.resposta.conteudo)))
            self.pedido_numero = int(transacao["reference"])
            pedido_pagamento = self.cria_entidade_pagador('PedidoPagamento', loja_id=self.configuracao.loja_id, pedido_numero=self.pedido_numero, codigo_pagamento=self.configuracao.meio_pagamento.codigo)
            pedido_pagamento.preencher_do_banco()
            detalhes = []
            if 'code' in transacao:
                if pedido_pagamento.transacao_id:
                    detalhes.append('Pedido tem transacao_id ({})'.format(pedido_pagamento.transacao_id))
                    if transacao['code'] == pedido_pagamento.transacao_id:
                        detalhes.append(u'transaction.code ({}) é igual ao pedido.transacao_id ({})'.format(transacao['code'], pedido_pagamento.transacao_id))
                        self._define_valor_e_situacao(transacao)
                    else:
                        detalhes.append(u'transaction.code ({}) é diferente ao pedido.transacao_id ({})'.format(transacao['code'], pedido_pagamento.transacao_id))
                else:
                    detalhes.append(u'Pedido não tem transacao_id ({})'.format(pedido_pagamento.transacao_id))
                    self.dados_pagamento['transacao_id'] = transacao['code']
                    self._define_valor_e_situacao(transacao)
                self.resultado = {'resultado': 'OK', 'detalhes': detalhes}
            else:
                self.resultado = {'resultado': 'ERRO', 'detalhes': [u'PagSeguro não enviou transaction.code']}
        else:
            self.resultado = {'resultado': 'ERRO', 'detalhes': [u'Não foi recebida uma resposta válida do PagSeguro']}

    def _gera_dados_envio(self):
        aplicacao = 'pagseguro-alternativo' if self.configuracao.aplicacao == 'pagseguro-alternativo' else 'pagseguro'
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
        return {
            'appKey': parametros['app_secret'],
            'appId': parametros['app_id'],
        }

    def obtem_informacoes_pagamento(self):
        if self.deve_obter_informacoes_pagseguro:
            self.dados_enviados = self._gera_dados_envio()
            self.resposta = self.conexao.get(self.url, dados=self.dados_enviados)

    @property
    def deve_obter_informacoes_pagseguro(self):
        return 'notificationCode' in self.dados

    @property
    def url(self):
        if 'notificationCode' in self.dados:
            return 'https://ws.{}pagseguro.uol.com.br/v3/transactions/notifications/{}'.format(self.sandbox, self.dados['notificationCode'])
        return ''


class AtualizaTransacoes(servicos.AtualizaTransacoes):
    def __init__(self, loja_id, dados):
        super(AtualizaTransacoes, self).__init__(loja_id, dados)
        self.url = 'https://ws.{}pagseguro.uol.com.br/v3/transactions'.format(self.sandbox)
        self.conexao = self.obter_conexao(formato_envio=requisicao.Formato.querystring, formato_resposta=requisicao.Formato.xml)
        self.atualizados = 0

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def _gera_dados_envio(self):
        initial_date = '{}T00:00'.format(self.dados['data_inicial'])
        final_date = '{}T23:59'.format(self.dados['data_final'])
        aplicacao = 'pagseguro-alternativo' if self.configuracao.aplicacao == 'pagseguro-alternativo' else 'pagseguro'
        parametros = self.cria_entidade_pagador('ParametrosDeContrato', loja_id=self.loja_id).obter_para(aplicacao)
        return {
            'appKey': parametros['app_secret'],
            'appId': parametros['app_id'],
            'initialDate': initial_date,
            'finalDate': final_date
        }

    def consulta_transacoes(self):
        self.dados_enviados = self._gera_dados_envio()
        self.resposta = self.conexao.get(self.url, dados=self.dados_enviados)

    def analisa_resultado_transacoes(self):
        if self.resposta.sucesso:
            transacoes = self.resposta.conteudo['transactionSearchResult'].get('transactions', [])
            if type(transacoes) is dict:
                self.dados_pedido = {
                    'situacao_pedido': SituacoesDePagamento.do_tipo(transacoes['transaction']['status']),
                    'pedido_numero': transacoes['transaction']['reference']
                }
            else:
                self.dados_pedido = []
                for transacao in transacoes:
                    self.dados_pedido.append({
                        'situacao_pedido': SituacoesDePagamento.do_tipo(transacao['transaction']['status']),
                        'pedido_numero': transacao['transaction']['reference']
                    })
        else:
            if 'errors' in self.resposta.conteudo:
                self.erros = self.resposta.conteudo