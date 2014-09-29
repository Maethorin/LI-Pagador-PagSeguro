//{% load filters %}
var url = '';
var $counter = null;
var segundos = 5;
$(function() {
    var $mercadoPagoMensagem = $(".mercadopago-mensagem");

    function iniciaContador() {
        $counter = $mercadoPagoMensagem.find(".segundos");
        setInterval('if (segundos > 0) { $counter.text(--segundos); }', 1000);
    }

    function enviaPagamento() {
        $mercadoPagoMensagem.find(".msg-danger").hide();
        $mercadoPagoMensagem.find(".msg-success").hide();
        $mercadoPagoMensagem.find(".msg-warning").show();
        $mercadoPagoMensagem.removeClass("alert-message-success");
        $mercadoPagoMensagem.removeClass("alert-message-danger");
        $mercadoPagoMensagem.addClass("alert-message-warning");
        var url_pagar = '{% url_loja "checkout_pagador" pedido.numero pagamento.id %}?next_url=' + window.location.href.split("?")[0];
        $.getJSON(url_pagar)
            .fail(function (data) {
                exibeMensagemErro(data.status, data.content);
            })
            .done(function (data) {
                if (data.sucesso) {
                    $("#aguarde").hide();
                    $("#redirecting").show();
                    url = data.content.url;
                    iniciaContador();
                    setTimeout('window.location = url;', 5000);
                }
                else {
                    if (data.status == 400) {
                        exibeMensagemErro(data.status, "Ocorreu um erro ao enviar os dados para o MercadoPago. Por favor, tente de novo");
                    }
                    else {
                        exibeMensagemErro(data.status, data.content);
                    }
                }
            });
    }

    $(".msg-danger").on("click", ".pagar", function() {
        enviaPagamento();
    });

    $(".msg-success").on("click", ".ir-mp", function() {
        window.location = url;
    });

    function exibeMensagemErro(status, mensagem) {
        $mercadoPagoMensagem.find(".msg-warning").hide();
        $mercadoPagoMensagem.toggleClass("alert-message-warning alert-message-danger");
        var $errorMessage = $("#errorMessage");
        $errorMessage.text(status + ": " + mensagem);
        $mercadoPagoMensagem.find(".msg-danger").show();
    }

    function exibeMensagemSucesso(situacao) {
        $mercadoPagoMensagem.find(".msg-warning").hide();
        $mercadoPagoMensagem.toggleClass("alert-message-warning alert-message-success");
        var $success = $mercadoPagoMensagem.find(".msg-success");
        $success.find("#redirecting").hide();
        if (situacao == "pago") {
            $success.find("#successMessage").show();
        }
        else {
            $success.find("#pendingMessage").show();
        }
        $success.show();
    }

    var pedidoPago = '{{ pedido.situacao_id }}' == '4';
    var pedidoAguardandoPagamento = '{{ pedido.situacao_id }}' == '2';

    if (window.location.search != "" && window.location.search.indexOf("failure") > -1) {
        exibeMensagemErro(500, "Pagamento cancelado no MercadoPago!");
    }
    else if (window.location.search != "" && window.location.search.indexOf("success") > -1 || pedidoPago) {
        exibeMensagemSucesso("pago");
    }
    else if (window.location.search != "" && window.location.search.indexOf("pending") > -1 || pedidoAguardandoPagamento) {
        exibeMensagemSucesso("aguardando");
    }
    else {
        enviaPagamento();
    }
});
