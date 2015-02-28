# -*- coding: utf-8 -*-

from pagador.reloaded import entidades
from pagador_pagseguro.reloaded import cadastro

CODIGO_GATEWAY = 1


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    _campos = ['ativo', 'aplicacao', 'codigo_autorizacao', 'valor_minimo_aceitado', 'valor_minimo_parcela', 'mostrar_parcelamento', 'maximo_parcelas', 'parcelas_sem_juros']
    _codigo_gateway = CODIGO_GATEWAY

    def __init__(self, loja_id, codigo_pagamento=None):
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento)
        self.preencher_do_gateway(self._codigo_gateway, self._campos)
        self.formulario = cadastro.FormularioPagSeguro()
        self.eh_aplicacao = True
