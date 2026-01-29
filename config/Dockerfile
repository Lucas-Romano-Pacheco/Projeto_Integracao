# Usando uma imagem leve do Python
FROM python:3.10-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependências
COPY requirements.txt .

# Instala as bibliotecas necessárias
RUN pip install --no-cache-dir -r requirements.txt

# Instala o Gunicorn (servidor de produção para o Flask)
RUN pip install gunicorn

# Copia todo o código para dentro do container
COPY . .

# Expõe a porta que o Render vai usar (padrão 10000)
EXPOSE 10000

# Comando para rodar o servidor em produção usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "servidor:app"]