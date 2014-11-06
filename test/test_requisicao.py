# -*- coding: utf-8 -*-
import mox
from pagador import settings
from pagador.envio.models import Pedido
from pagador_pagseguro.extensao.requisicao import EnviarPedido


class TestDadosEnvio(mox.MoxTestBase):
    def setUp(self):
        super(TestDadosEnvio, self).setUp()
        self.pedido = Pedido.objects.filter(conta_id=8)[0]
        self.enviar = EnviarPedido(self.pedido, {}, None)

    def test_valida_nome_sem_espaco(self):
        self.pedido.cliente.nome = "NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME x")

    def test_valida_nome_com_espaco_antes(self):
        self.pedido.cliente.nome = " NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME x")

    def test_valida_nome_com_espaco_depois(self):
        self.pedido.cliente.nome = "NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME x")

    def test_valida_nome_com_e_comercial(self):
        self.pedido.cliente.nome = "NOME & NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME E NOME")

    def test_valida_nome_com_ponto_de_interrogacao(self):
        self.pedido.cliente.nome = "NOME ? NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME NOME")

    def test_valida_nome_com_espaco_duplo(self):
        self.pedido.cliente.nome = "NOME  NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME NOME")

    def test_valida_nome_com_espcaco_triplo(self):
        self.pedido.cliente.nome = "NOME   NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME NOME")

    def test_valida_nome_com_espaco_duplo_a_frente(self):
        self.pedido.cliente.nome = "  NOME NOME"
        self.enviar.nome_do_cliente.should.be.equal("NOME NOME")

    def test_valida_nome_com_espaco_duplo_a_atras(self):
        self.pedido.cliente.nome = "NOME NOME  "
        self.enviar.nome_do_cliente.should.be.equal("NOME NOME")

    def test_valida_nome_com_utf_8(self):
        self.pedido.cliente.nome = u"Calçado Só"
        self.enviar.nome_do_cliente.should.be.equal("Calcado So")
