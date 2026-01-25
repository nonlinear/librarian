#!/bin/zsh
# Mata qualquer hugo rodando
pkill -f 'hugo serve'
# Atualiza o repo
git pull
# Inicia hugo em background
nohup hugo serve -D > hugo.log 2>&1 &
# Aguarda 3 segundos
sleep 3
# Abre o navegador
open http://localhost:1313/${fileBasenameNoExtension}
