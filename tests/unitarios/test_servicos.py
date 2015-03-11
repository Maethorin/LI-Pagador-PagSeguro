# -*- coding: utf-8 -*-
import unittest

import mock

from pagador_pagseguro import servicos


class PagSeguroInstalacaoMeioPagamento(unittest.TestCase):
    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_instanciar_com_loja_id(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.loja_id.should.be.equal(8)

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_definir_usa_alt(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        instalador.usa_alt.should.be.truthy

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_definir_aplicacao(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.aplicacao.should.be.equal('pagseguro')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_definir_aplicacao_com_usa_alt(self, parametros_mock):
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        instalador.aplicacao.should.be.equal('pagseguro-alternativo')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_obter_parametros(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        servicos.InstalaMeioDePagamento(8, {'dados': 1})
        parametros_mock.assert_called_with(loja_id=8)
        parametro.obter_para.assert_called_with('pagseguro')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_obter_parametros_alternativos(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        servicos.InstalaMeioDePagamento(8, {'dados': 1, 'ua': 1})
        parametro.obter_para.assert_called_with('pagseguro-alternativo')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_definir_parametros(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.app_key.should.be.equal('1')
        instalador.app_id.should.be.equal('2')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.servicos.InstalaMeioDePagamento.obter_conexao')
    def test_deve_definir_conexao(self, obter_mock, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        obter_mock.return_value = 'conexao'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.conexao.should.be.equal('conexao')
        obter_mock.assert_called_with(formato_envio='application/xml', formato_resposta='application/xml')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.servicos.settings', autospec=True)
    def test_nao_deve_ser_sandbox_em_producao(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'production'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.servicos.settings', autospec=True)
    def test_deve_ser_sandbox_em_desenvolvimento(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'development'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('sandbox.')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    @mock.patch('pagador_pagseguro.servicos.InstalaMeioDePagamento.obter_conexao')
    @mock.patch('pagador_pagseguro.servicos.settings', autospec=True)
    def test_deve_ser_sandbox_em_local(self, settings_mock, obter_mock, parametros_mock):
        settings_mock.ENVIRONMENT = 'local'
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.sandbox.should.be.equal('sandbox.')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
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

    @mock.patch('pagador.entidades.ParametrosDeContrato')
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

    @mock.patch('pagador.entidades.ParametrosDeContrato')
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

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_obter_dados_pagseguro(self, parametros_mock):
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

    @mock.patch('pagador.entidades.ParametrosDeContrato')
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

    @mock.patch('pagador.entidades.ParametrosDeContrato')
    def test_deve_dar_erro_se_pagseguro_nao_enviar_notification_code(self, parametros_mock):
        parametro = mock.MagicMock()
        parametro.obter_para.return_value = {'app_secret': '1', 'app_id': '2'}
        parametros_mock.return_value = parametro
        instalador = servicos.InstalaMeioDePagamento(8, {'dados': 1})
        instalador.obter_dados.when.called_with().should.throw(instalador.InstalacaoNaoFinalizada, u'O PagSeguro não retornou o código de autorização válido. Por favor, verifique a sua conta no PagSeguro e tente de novo.')

    @mock.patch('pagador.entidades.ParametrosDeContrato')
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
    @mock.patch('pagador.entidades.ParametrosDeContrato', mock.MagicMock())
    def test_deve_definir_lista_campos(self):
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.campos.should.be.equal(['codigo_autorizacao', 'aplicacao'])

    @mock.patch('pagador.entidades.ParametrosDeContrato', mock.MagicMock())
    def test_deve_retornar_redirect_pra_pagina_autorizacoes(self):
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.desinstalar({}).should.be.equal({'url': 'https://sandbox.pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'})

    @mock.patch('pagador.entidades.ParametrosDeContrato', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.settings', autospec=True)
    def test_nao_deve_usar_sandbox_na_url_se_for_production(self, settings_mock):
        settings_mock.ENVIRONMENT = 'production'
        instalador = servicos.InstalaMeioDePagamento(8, {})
        instalador.desinstalar({}).should.be.equal({'url': 'https://pagseguro.uol.com.br/aplicacao/listarAutorizacoes.jhtml'})


class PagSeguroCredenciais(unittest.TestCase):
    def test_deve_definir_propriedades(self):
        credenciador = servicos.Credenciador(configuracao=mock.MagicMock())
        credenciador.tipo.should.be.equal(credenciador.TipoAutenticacao.query_string)
        credenciador.chave.should.be.equal('authorizationCode')

    def test_deve_retornar_credencial_baseado_no_usuario(self):
        configuracao = mock.MagicMock(codigo_autorizacao='codigo-autorizacao')
        credenciador = servicos.Credenciador(configuracao=configuracao)
        credenciador.obter_credenciais().should.be.equal('codigo-autorizacao')


class PagSeguroSituacoesPagamento(unittest.TestCase):
    def test_deve_retornar_aguadando_para_1(self):
        servicos.SituacoesDePagamento.do_tipo('1').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO)

    def test_deve_retornar_em_analise_para_2(self):
        servicos.SituacoesDePagamento.do_tipo('2').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE)

    def test_deve_retornar_pago_para_3(self):
        servicos.SituacoesDePagamento.do_tipo('3').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_retornar_em_disputa_para_5(self):
        servicos.SituacoesDePagamento.do_tipo('5').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA)

    def test_deve_retornar_devolvido_para_6(self):
        servicos.SituacoesDePagamento.do_tipo('6').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO)

    def test_deve_retornar_cancelado_para_7(self):
        servicos.SituacoesDePagamento.do_tipo('7').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO)

    def test_deve_retornar_chargeback_para_8(self):
        servicos.SituacoesDePagamento.do_tipo('8').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PAGTO_CHARGEBACK)

    def test_deve_retornar_none_para_desconhecido(self):
        servicos.SituacoesDePagamento.do_tipo('zas').should.be.none


class PagSeguroEntregaPagamento(unittest.TestCase):
    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_tem_malote(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.tem_malote.should.be.truthy

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_faz_http(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.faz_http.should.be.truthy

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_resposta(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta.should.be.none

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_url_com_sandbox(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.url.should.be.equal('https://ws.sandbox.pagseguro.uol.com.br/v2/checkout')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.sandbox', '')
    def test_deve_definir_url_sem_sandbox(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.url.should.be.equal('https://ws.pagseguro.uol.com.br/v2/checkout')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao')
    def test_deve_montar_conexao(self, obter_mock):
        obter_mock.return_value = 'conexao'
        entregador = servicos.EntregaPagamento(1234)
        entregador.conexao.should.be.equal('conexao')
        obter_mock.assert_called_with(formato_envio='application/x-www-form-urlencoded', formato_resposta='application/xml')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagseguro.servicos.Credenciador')
    def test_deve_definir_credenciais(self, credenciador_mock):
        entregador = servicos.EntregaPagamento(1234)
        credenciador_mock.return_value = 'credenciador'
        entregador.configuracao = 'configuracao'
        entregador.define_credenciais()
        entregador.conexao.credenciador.should.be.equal('credenciador')
        credenciador_mock.assert_called_with(configuracao='configuracao')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = 'malote-como-dicionario'
        entregador.conexao = mock.MagicMock()
        entregador.conexao.post.return_value = 'resposta'
        entregador.envia_pagamento()
        entregador.dados_enviados.should.be.equal('malote-como-dicionario')
        entregador.resposta.should.be.equal('resposta')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_usar_post_ao_enviar_pagamento(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = 'malote-como-dicionario'
        entregador.conexao = mock.MagicMock()
        entregador.envia_pagamento()
        entregador.conexao.post.assert_called_with(entregador.url, 'malote-como-dicionario')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_dados_de_pagamento(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador._processa_resposta = mock.MagicMock()
        entregador._processa_resposta.return_value = 'resposta-processada'
        entregador.processa_dados_pagamento()
        entregador._processa_resposta.assert_called_with()
        entregador.resultado.should.be.equal('resposta-processada')

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_resposta_sucesso(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta = mock.MagicMock(conteudo={'checkout': {'code': 'code-checkout'}}, status_code=200, sucesso=True, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False)
        entregador.processa_dados_pagamento()
        entregador.resultado.should.be.equal({'url': 'https://sandbox.pagseguro.uol.com.br/v2/checkout/payment.html?code=code-checkout'})

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_resposta_erro(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta = mock.MagicMock(conteudo={}, status_code=500, sucesso=False, erro_servidor=True, timeout=False, nao_autenticado=False, nao_autorizado=False)
        entregador.processa_dados_pagamento()
        entregador.resultado.should.be.equal({'mensagem': u'O servidor do PagSeguro está indisponível nesse momento.', 'status_code': 500})

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_resposta_timeout(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta = mock.MagicMock(conteudo={}, status_code=408, sucesso=False, erro_servidor=False, timeout=True, nao_autenticado=False, nao_autorizado=False)
        entregador.processa_dados_pagamento()
        entregador.resultado.should.be.equal({'mensagem': u'O servidor do PagSeguro não respondeu em tempo útil.', 'status_code': 408})

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_resposta_nao_autenticado(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta = mock.MagicMock(conteudo={}, status_code=401, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=True, nao_autorizado=False)
        entregador.processa_dados_pagamento()
        entregador.resultado.should.be.equal({'mensagem': u'Autenticação da loja com o PagSeguro Falhou. Contate o SAC da loja.', 'status_code': 401})

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_processar_resposta_nao_autorizado(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.resposta = mock.MagicMock(conteudo={}, status_code=400, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=True)
        entregador.processa_dados_pagamento()
        entregador.resultado.should.be.equal({'mensagem': u'Autenticação da loja com o PagSeguro Falhou. Contate o SAC da loja.', 'status_code': 400})

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_disparar_erro_se_resposta_vier_com_status_nao_conhecido_e_sem_erro(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.pedido = mock.MagicMock(numero=123)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = 'malote'
        entregador.resposta = mock.MagicMock(conteudo={'erro': 'zas'}, status_code=666, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False)
        entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_disparar_erro_se_tiver_erro_na_reposta(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.pedido = mock.MagicMock(numero=123)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = 'malote'
        entregador.resposta = mock.MagicMock(
            conteudo={
                'errors': {'error': {'code': 'code1', 'message': 'message1'}}
            },
            status_code=500, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False
        )
        entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)

    @mock.patch('pagador_pagseguro.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_disparar_erro_se_tiver_lista_de_erros_na_reposta(self):
        entregador = servicos.EntregaPagamento(1234)
        entregador.pedido = mock.MagicMock(numero=123)
        entregador.malote = mock.MagicMock()
        entregador.malote.to_dict.return_value = 'malote'
        entregador.resposta = mock.MagicMock(
            conteudo={
                'errors': [
                    {'error': {'code': 'code1', 'message': 'message1'}},
                    {'error': {'code': 'code2', 'message': 'message2'}}
                ]
            },
            status_code=500, sucesso=False, erro_servidor=False, timeout=False, nao_autenticado=False, nao_autorizado=False
        )
        entregador.processa_dados_pagamento.when.called_with().should.throw(entregador.EnvioNaoRealizado)
