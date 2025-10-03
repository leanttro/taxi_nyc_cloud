timeout = 180  # Aumenta o tempo limite de inicialização para 180 segundos (3 minutos)
workers = 1    # Garante que apenas um processo Flask seja iniciado para economizar memória
bind = '0.0.0.0:10000' # Mantém a porta padrão do Render
