# Usa uma imagem oficial do Python como base.
FROM python:3.9-slim

# Define o diretório de trabalho dentro do contêiner.
WORKDIR /app

# Copia o arquivo de dependências e instala-as.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do seu projeto.
COPY . .

# Define a porta que a aplicação irá expor.
EXPOSE 5000

# Comando para rodar a aplicação quando o contêiner for iniciado.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]