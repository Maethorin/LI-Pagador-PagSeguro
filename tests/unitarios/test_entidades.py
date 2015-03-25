# -*- coding: utf-8 -*-
from decimal import Decimal
import unittest

import mock

from pagador_pagseguro import entidades


class PagSeguroConfiguracaoMeioPagamento(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PagSeguroConfiguracaoMeioPagamento, self).__init__(*args, **kwargs)
        self.campos = ['ativo', 'aplicacao', 'codigo_autorizacao', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
        self.codigo_gateway = 1

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_os_campos_especificos_na_classe(self):
        entidades.ConfiguracaoMeioPagamento(234).campos.should.be.equal(self.campos)

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_codigo_gateway(self):
        entidades.ConfiguracaoMeioPagamento(234).codigo_gateway.should.be.equal(self.codigo_gateway)

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_preencher_gateway_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        preencher_mock.assert_called_with(configuracao, self.codigo_gateway, self.campos)

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_definir_formulario_na_inicializacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.formulario.should.be.a('pagador_pagseguro.cadastro.FormularioPagSeguro')

    @mock.patch('pagador_pagseguro.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ser_aplicacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_aplicacao.should.be.truthy


class PagSeguroMontandoMalote(unittest.TestCase):
    def test_deve_definir_tipo_de_envio_pac(self):
        entidades.TipoEnvio('pac').valor.should.be.equal(1)

    def test_deve_definir_tipo_de_envio_sedex(self):
        entidades.TipoEnvio('sedex').valor.should.be.equal(2)

    def test_deve_definir_tipo_de_envio_outro(self):
        entidades.TipoEnvio('outro').valor.should.be.equal(3)

    def test_malote_deve_ter_propriedades(self):
        entidades.Malote('configuracao').to_dict().should.be.equal({'appId': None, 'appKey': None, 'currency': None, 'extraAmount': None, 'notificationURL': None, 'redirectURL': None, 'reference': None, 'senderAreaCode': None, 'senderEmail': None, 'senderName': None, 'senderPhone': None, 'shippingAddressCity': None, 'shippingAddressComplement': None, 'shippingAddressCountry': 'BRA', 'shippingAddressDistrict': None, 'shippingAddressNumber': None, 'shippingAddressPostalCode': None, 'shippingAddressState': None, 'shippingAddressStreet': None, 'shippingCost': None, 'shippingType': None})

    def test_deve_montar_conteudo(self):
        malote = entidades.Malote(mock.MagicMock(loja_id=8))
        pedido = mock.MagicMock(
            cliente_telefone=('21', '99999999'),
            numero=1234,
            cliente_nome_ascii='Nome',
            forma_envio='pac',
            cliente={'email': 'cliente@email.com'},
            valor_envio=Decimal('14.00'),
            valor_desconto=Decimal('4.00'),
            endereco_entrega={
                'nome': u'Nome endereço entrega', 'endereco': 'Rua entrega', 'numero': '51', 'complemento': 'lt 51',
                'bairro': 'Bairro', 'cidade': 'Cidade', 'cep': '12908-212', 'estado': 'RJ'
            },
            itens=[
                mock.MagicMock(nome='Produto 1', sku='PROD01', quantidade=1, preco_venda=Decimal('40.00'), url_produto='url-prd-1'),
                mock.MagicMock(nome='Produto 2', sku='PROD02', quantidade=1, preco_venda=Decimal('50.00'), url_produto='url-prd-2'),
            ]
        )
        dados = {'next_url': 'url-next'}
        parametros = {'app_secret': 'app-secret', 'app_id': 'app-id'}
        malote.monta_conteudo(pedido, parametros, dados)
        malote.to_dict().should.be.equal({'appId': 'app-id', 'appKey': 'app-secret', 'currency': 'BRL', 'extraAmount': '-4.00', 'itemAmount1': '40.00', 'itemAmount2': '50.00', 'itemDescription1': 'Produto 1', 'itemDescription2': 'Produto 2', 'itemId1': 'PROD01', 'itemId2': 'PROD02', 'itemQuantity1': 1, 'itemQuantity2': 1, 'notificationURL': 'http://localhost:5000/pagador/meio-pagamento/pagseguro/retorno/8/notificacao', 'redirectURL': 'http://localhost:5000/pagador/meio-pagamento/pagseguro/retorno/8/resultado?next_url=url-next&referencia=1234', 'reference': 1234, 'senderAreaCode': '21', 'senderEmail': 'cliente@email.com', 'senderName': 'Nome', 'senderPhone': '99999999', 'shippingAddressCity': 'Cidade', 'shippingAddressComplement': 'lt 51', 'shippingAddressCountry': 'BRA', 'shippingAddressDistrict': 'Bairro', 'shippingAddressNumber': '51', 'shippingAddressPostalCode': '12908-212', 'shippingAddressState': 'RJ', 'shippingAddressStreet': 'Rua entrega', 'shippingCost': '14.00', 'shippingType': 1})