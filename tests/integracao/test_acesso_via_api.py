# -*- coding: utf-8 -*-
import json
import mock
from li_common.padroes import extensibilidade

from tests.base import TestBase

extensibilidade.SETTINGS.EXTENSOES = {
    'pagseguro': 'pagador_pagseguro'
}


class PagSeguroConfiguracaoMeioDePagamentoDaLoja(TestBase):
    url = '/loja/8/meio-pagamento/pagseguro/configurar'

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_obter_dados_pagseguro(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.to_dict.return_value = 'PAGSEGURO'
        response = self.app.get(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'configuracao_pagamento': u'PAGSEGURO'}})
        response.status_code.should.be.equal(200)
        configuracao_mock.assert_called_with(loja_id=8, codigo_pagamento='pagseguro', eh_listagem=False)

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_grava_dados_pagseguro(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.to_dict.return_value = 'PAGSEGURO'
        response = self.app.post(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'configuracao_pagamento': u'PAGSEGURO'}})
        response.status_code.should.be.equal(200)
        configuracao.salvar_formulario.assert_called_with({'token': u'ZES'})


class InstalacaoMeioDePagamentoDaLoja(TestBase):
    url = '/loja/8/meio-pagamento/pagseguro/instalar'

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_gravar_dados_pagseguro(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.instalar.return_value = 'PAGSEGURO'
        response = self.app.get(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'conteudo': u'PAGSEGURO'}})
        response.status_code.should.be.equal(200)
        configuracao.instalar.assert_called_with({'token': u'ZES'})

    @mock.patch('api_pagador.recursos.redirect')
    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_redirecionar_se_tiver_redirect_no_conteudo(self, configuracao_mock, redirect_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.instalar.return_value = {'mensagem': 'PAGSEGURO', 'redirect': 'url-redirect'}
        redirect_mock.return_value = 'ZAS'
        self.app.get(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        redirect_mock.assert_called_with('url-redirect?mensagem=PAGSEGURO', code=301)

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_obter_url_autorizacao_pagseguro(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.instalar.return_value = 'url-ativador'
        response = self.app.put(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'conteudo': u'url-ativador'}})
        response.status_code.should.be.equal(200)
        configuracao.instalar.assert_called_with({'token': u'ZES'})


class DesinstalacaoMeioDePagamentoDaLoja(TestBase):
    url = '/loja/8/meio-pagamento/pagseguro/instalar'

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento')
    def test_deve_remover_dados_pagseguro(self, configuracao_mock):
        configuracao = mock.MagicMock()
        configuracao_mock.return_value = configuracao
        configuracao.desinstalar.return_value = 'PAGSEGURO-OUT'
        response = self.app.delete(self.url, follow_redirects=True, data={'token': 'ZES'}, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'conteudo': u'PAGSEGURO-OUT'}})
        response.status_code.should.be.equal(200)
        configuracao.desinstalar.assert_called_with({'token': u'ZES'})


class PagSeguroEnviandoPagamento(TestBase):
    url = '/loja/8/meio-pagamento/pagseguro/enviar/1234/1'

    @mock.patch('pagador.servicos.GerenciaPedido', mock.MagicMock())
    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento')
    def test_deve_enviar_pagamento(self, entrega_mock):
        entrega_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'pagamento-enviado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'status_code': 200, u'zas': u'pagamento-enviado'}})

    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador.servicos.GerenciaPedido')
    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento')
    def test_deve_dar_erro_se_nao_atualizar_pedido(self, entrega_mock, gerencia_mock):
        gerencia_mock.return_value = mock.MagicMock(resultado={'sucesso': False})
        entrega_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'pagamento-enviado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        response.status_code.should.be.equal(500)
        json.loads(response.data).should.be.equal({u'erro_servidor': {u'status_code': 500, u'zas': u'pagamento-enviado'}, u'metadados': {u'api': u'API Pagador', u'resultado': u'erro_servidor', u'versao': u'1.0'}})


class PagSeguroRegistrandoResultado(TestBase):
    url = '/meio-pagamento/pagseguro/retorno/8/resultado'

    @mock.patch('pagador.servicos.GerenciaPedido', mock.MagicMock())
    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.RegistraResultado')
    def test_deve_registrar_retorno(self, registra_mock):
        registra_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'resultado-registrado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'status_code': 200, u'zas': u'resultado-registrado'}})

    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador.servicos.GerenciaPedido')
    @mock.patch('pagador_pagseguro.servicos.RegistraResultado')
    def test_deve_dar_erro_se_nao_atualizar_pedido(self, entrega_mock, gerencia_mock):
        gerencia_mock.return_value = mock.MagicMock(resultado={'sucesso': False})
        entrega_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'pagamento-registrado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        response.status_code.should.be.equal(500)
        json.loads(response.data).should.be.equal({u'erro_servidor': {u'status_code': 500, u'zas': u'pagamento-registrado'}, u'metadados': {u'api': u'API Pagador', u'resultado': u'erro_servidor', u'versao': u'1.0'}})


class PagSeguroRegistrandoNotificacao(TestBase):
    url = '/meio-pagamento/pagseguro/retorno/8/notificacao'

    @mock.patch('pagador.servicos.GerenciaPedido', mock.MagicMock())
    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.RegistraNotificacao')
    def test_deve_registrar_notificacao(self, registra_mock):
        registra_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'notificacao-registrado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        json.loads(response.data).should.be.equal({u'metadados': {u'api': u'API Pagador', u'resultado': u'sucesso', u'versao': u'1.0'}, u'sucesso': {u'status_code': 200, u'zas': u'notificacao-registrado'}})

    @mock.patch('pagador.servicos.GravaEvidencia', mock.MagicMock())
    @mock.patch('pagador.servicos.GerenciaPedido')
    @mock.patch('pagador_pagseguro.servicos.RegistraNotificacao')
    def test_deve_dar_erro_se_nao_atualizar_pedido(self, entrega_mock, gerencia_mock):
        gerencia_mock.return_value = mock.MagicMock(resultado={'sucesso': False})
        entrega_mock.return_value = mock.MagicMock(redirect_para=None, resultado={'zas': 'pagamento-registrado'})
        response = self.app.post(self.url, follow_redirects=True, headers={'authorization': 'chave_aplicacao CHAVE-TESTE'})
        response.status_code.should.be.equal(500)
        json.loads(response.data).should.be.equal({u'erro_servidor': {u'status_code': 500, u'zas': u'pagamento-registrado'}, u'metadados': {u'api': u'API Pagador', u'resultado': u'erro_servidor', u'versao': u'1.0'}})
