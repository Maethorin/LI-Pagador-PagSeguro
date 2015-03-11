LI-Pagador-PagSeguro
====================

LI-Pagador-PagSeguro

## Versão:

[![PyPi version](https://pypip.in/version/li-pagador-pagseguro/badge.svg?text=versão)](https://pypi.python.org/pypi/li-pagador-pagseguro)
[![PyPi downloads](https://pypip.in/download/li-pagador-pagseguro/badge.svg)](https://pypi.python.org/pypi/li-pagador-pagseguro)


## Build Status

### Master

[![Build Status](https://travis-ci.org/lojaintegrada/LI-Pagador-PagSeguro.svg?branch=master)](https://travis-ci.org/lojaintegrada/LI-Pagador-PagSeguro)
[![Coverage Status](https://coveralls.io/repos/lojaintegrada/LI-Pagador-PagSeguro/badge.svg?branch=master)](https://coveralls.io/r/lojaintegrada/LI-Pagador-PagSeguro?branch=master)

### Pagador Reloaded

[![Build Status](https://travis-ci.org/lojaintegrada/LI-Pagador-PagSeguro.svg?branch=pagador-reloaded)](https://travis-ci.org/lojaintegrada/LI-Pagador-PagSeguro)
[![Coverage Status](https://coveralls.io/repos/lojaintegrada/LI-Pagador-PagSeguro/badge.svg?branch=pagador-reloaded)](https://coveralls.io/r/lojaintegrada/LI-Pagador-PagSeguro?branch=pagador-reloaded)


Guia de implementação de notificações:

https://pagseguro.uol.com.br/v3/guia-de-integracao/api-de-notificacoes.html#v3-item-servico-de-notificacoes

Exemplo de chamada que a api responde:

http://localhost:5000/pagador/meio-pagamento/pagseguro/retorno/8/notificacao?notificationCode=FD6D4DCF92A092A0F21DD4FA1FB8A4F9E7D9&notificationType=transaction