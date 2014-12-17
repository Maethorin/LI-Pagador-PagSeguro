# -*- coding: utf-8 -*-
import os

from pagador.configuracao.cadastro import CampoFormulario, FormularioBase, TipoDeCampo, CadastroBase, SelecaoBase, caminho_para_template
from pagador.configuracao.cliente import Script, TipoScript

eh_aplicacao = True


def caminho_do_arquivo_de_template(arquivo):
    return caminho_para_template(arquivo, meio_pagamento='pagseguro')


class MeioPagamentoCadastro(CadastroBase):
    @property
    def registro(self):
        script = Script(tipo=TipoScript.html, nome="registro")
        script.adiciona_linha(u'Ainda não tem conta no PagSeguro?')
        script.adiciona_linha(u'<a href="//pagseguro.uol.com.br/" title="Criar conta PagSeguro" class="btn btn-info btn-xs" target="_blank">cadastre-se</a>')
        return script

    @property
    def descricao(self):
        script = Script(tipo=TipoScript.html, nome="descricao")
        script.adiciona_linha(u'<p>Para que o PagSeguro funcione corretamenteo, siga o seguintes passos:</p>')
        script.adiciona_linha(u'<p>1. Tenha uma conta no PagSeguro do tipo Vendedor. <a href="https://pagseguro.uol.com.br/account/viewDetails.jhtml" target="_blank">Clique aqui</a> para fazer a mudança;</p>')
        script.adiciona_linha(u'<p>2. No PagSeguro, entre no menu <strong>Preferências -> Frete</strong> e depois marque a opção <strong>Frete adicional com valor fixo</strong> e coloque o valor de <strong>R$ 0,00 reais</strong> e clique em <strong>CONFIRMAR</strong> no final da página.</p>')
        script.adiciona_linha(u'<small>A integração com o PagSeguro gera custos de operação que são repassados para a plataforma pelo PagSeguro (1%). O lojista não paga comissão para a plataforma. Isso não altera o valor da taxa cobrada às lojas pelo PagSeguro pelas transações, de 4,79% + R$0,40 (taxa exclusiva para transações através da plataforma).</small>')
        return script

    def to_dict(self):
        return {
            "html": [
                self.registro.to_dict(),
                self.descricao.to_dict(),
            ]
        }

PARCELAS = [(x, x) for x in range(1, 19)]
PARCELAS.insert(0, (18, "Todas"))


class Formulario(FormularioBase):
    mostrar_parcelamento = CampoFormulario("mostrar_parcelamento", "Marque para mostrar o parcelamento na listagem e na página do produto.", tipo=TipoDeCampo.boleano, requerido=False, ordem=1)
    maximo_parcelas = CampoFormulario("maximo_parcelas", "Máximo de parcelas", tipo=TipoDeCampo.escolha, requerido=False, ordem=2, texto_ajuda=u"Quantidade máxima de parcelas para esta forma de pagamento.", opcoes=PARCELAS)
    parcelas_sem_juros = CampoFormulario("parcelas_sem_juros", "Parcelas sem juros", tipo=TipoDeCampo.escolha, requerido=False, ordem=3, texto_ajuda=u"Número de parcelas sem juros para esta forma de pagamento.", opcoes=PARCELAS)


class MeioPagamentoEnvio(object):
    @property
    def css(self):
        return Script(tipo=TipoScript.css, caminho_arquivo=caminho_do_arquivo_de_template("style.css"))

    @property
    def function_enviar(self):
        return Script(tipo=TipoScript.javascript, eh_template=True, caminho_arquivo=caminho_do_arquivo_de_template("javascript.js"))

    @property
    def mensagens(self):
        return Script(tipo=TipoScript.html, caminho_arquivo=caminho_do_arquivo_de_template("mensagens.html"), eh_template=True)

    def to_dict(self):
        return [
            self.css.to_dict(),
            self.function_enviar.to_dict(),
            self.mensagens.to_dict()
        ]


class MeioPagamentoSelecao(SelecaoBase):
    selecao = Script(tipo=TipoScript.html, nome="selecao", caminho_arquivo=caminho_do_arquivo_de_template("selecao.html"), eh_template=True)

    def to_dict(self):
        return [
            self.selecao.to_dict()
        ]
