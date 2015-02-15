# -*- coding: utf-8 -*-

from pagador.reloaded import entidades
from pagador_pagseguro.reloaded import cadastro


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    _campos = ['ativo', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
    _codigo_gateway = 1

    def __init__(self, loja_id):
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id)
        self.preencher_do_gateway(self._codigo_gateway, self._campos)
        self.formulario = cadastro.FormularioPagSeguro()
        self.eh_aplicacao = True
