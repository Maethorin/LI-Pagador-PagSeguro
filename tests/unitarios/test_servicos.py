# -*- coding: utf-8 -*-
import unittest
import mock
from pagador_pagseguro.reloaded import servicos


class PagSeguroInstalacaoMeioPagamento(unittest.TestCase):
    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_instanciar_com_loja_id(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.loja_id.should.be.equal(8)

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_definir_usa_alt(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        instalador.usa_alt.should.be.truthy

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_definir_aplicacao(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.aplicacao.should.be.equal('pagseguro')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_definir_aplicacao_com_usa_alt(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        instalador.aplicacao.should.be.equal('pagseguro-alternativo')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_obter_parametros(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        servicos.InstalaMeioDePagamento(8, {'dados': 1})
        parametros_mock.assert_called_with(loja_id=8)
        parametro.obter_para.assert_called_with('pagseguro')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_obter_parametros_alternativos(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        parametro.obter_para.assert_called_with('pagseguro-alternativo')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_definir_parametros(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.app_key.should.be.equal('1')
        instalador.app_id.should.be.equal('2')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.reloaded.servicos.InstalaMeioDePagamento.obter_conexao')
    def test_deve_definir_conexao(self, obter_mock, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        obter_mock.return_value = 'conexao'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.conexao.should.be.equal('conexao')
        obter_mock.assert_called_with(formato_envio='application/xml', formato_resposta='application/xml')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.reloaded.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.reloaded.servicos.settings', autospec=True)
    def test_nao_deve_ser_sandbox_em_producao(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'production'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.reloaded.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.reloaded.servicos.settings', autospec=True)
    def test_deve_ser_sandbox_em_desenvolvimento(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'development'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('sandbox.')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.reloaded.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.reloaded.servicos.settings', autospec=True)
    def test_deve_ser_sandbox_em_local(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'local'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('sandbox.')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_retornar_url_autorizacao_com_post_sucesso(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'next_url': 'url-next'})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = True
        reposta.conteudo = {'authorizationRequest': {'code': 'codigo_retorno'}}
        instalador.conexao.post.return_value = reposta
        instalador.montar_url_autorizacao().should.be.equal('https://sandbox.pagseguro.uol.com.br/v2/authorization/request.jhtml?code=codigo_retorno')
        instalador.conexao.post.assert_called_with('https://ws.sandbox.pagseguro.uol.com.br/v2/authorizations/request?appKey=1&appId=2', dados=u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><authorizationRequest><redirectURL><![CDATA[http://localhost:5000/pagador/loja/8/meio-pagamento/pagseguro/instalar?next_url=url-next&fase_atual=2]]></redirectURL><reference>8</reference><permissions><code>CREATE_CHECKOUTS</code><code>SEARCH_TRANSACTIONS</code><code>RECEIVE_TRANSACTION_NOTIFICATIONS</code></permissions></authorizationRequest>')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_disparar_erro_se_nao_tiver_next_url(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = True
        reposta.conteudo = {'authorizationRequest': {'code': 'codigo_retorno'}}
        instalador.conexao.post.return_value = reposta
        instalador.montar_url_autorizacao.when.called_with().should.throw(servicos.InstalaMeioDePagamento.InstalacaoNaoFinalizada, u'Você precisa informar a url de redirecionamento na volta do PagSeguro na chave next_url do parâmetro dados.')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_disparar_erro_se_nao_conseguir_obter_code(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'next_url': 'url-next'})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = False
        reposta.conteudo = 'pagseguro conteudo'
        reposta.status_code = 'pagseguro status_code'
        instalador.conexao.post.return_value = reposta
        instalador.montar_url_autorizacao.when.called_with().should.throw(instalador.InstalacaoNaoFinalizada, u'Erro ao entrar em contato com o PagSeguro. Código: pagseguro status_code - Resposta: pagseguro conteudo')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_obter_dados_do_pagseguro(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'notificationCode': 'notification-code'})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = True
        reposta.conteudo = {'authorization': {'code': 'codigo_autorizacao'}}
        instalador.conexao.get.return_value = reposta
        instalador.obter_dados().should.be.equal({'aplicacao': 'pagseguro', 'codigo_autorizacao': 'codigo_autorizacao'})

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_chamar_get_com_url_certa(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'notificationCode': 'notification-code'})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = True
        reposta.conteudo = {'authorization': {'code': 'codigo_autorizacao'}}
        instalador.conexao.get.return_value = reposta
        instalador.obter_dados()
        instalador.conexao.get.assert_called_with('https://ws.sandbox.pagseguro.uol.com.br/v2/authorizations/notifications/notification-code/?appKey=1&appId=2')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_dar_erro_se_pagseguro_nao_enviar_notification_code(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.obter_dados.when.called_with().should.throw(instalador.InstalacaoNaoFinalizada, u'O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo.')

    @mock.patch('pagador.reloaded.entidades.ParametrosDeContrato')
    def test_deve_disparar_erro_se_reposta_nao_for_sucesso(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'notificationCode': 'notification-code'})
        instalador.conexao = mock.MagicMock()
        reposta = mock.MagicMock()
        reposta.sucesso = False
        reposta.conteudo = 'pagseguro conteudo'
        reposta.status_code = 'pagseguro status_code'
        instalador.conexao.get.return_value = reposta
        instalador.obter_dados.when.called_with().should.throw(instalador.InstalacaoNaoFinalizada, u'Erro ao entrar em contato com o PagSeguro. Código: pagseguro status_code - Resposta: pagseguro conteudo')


class PagSeguroDesinstalacaoMeioPagamento(unittest.TestCase):
    def test_deve_definir_lista_de_campos(self):
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.campos.should.be.equal(['codigo_autorizacao', 'aplicacao'])

    def test_deve_retornar_redirect_pra_pagina_de_autorizacoes(self):
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.desinstalar({}).should.be.equal({'redirect': 'https://sandbox.pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'})

    @mock.patch('pagador_pagseguro.reloaded.servicos.settings', autospec=True)
    def test_nao_deve_usar_sandbox_na_url_se_for_production(self, settings_mock):
        settings_mock.ENVIRONMENT = 'production'
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.desinstalar({}).should.be.equal({'redirect': 'https://pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'})
