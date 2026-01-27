import requests

# 1. Configurações de Acesso
# Substitua pela URL da sua empresa (ex: https://suaempresa.sysaidit.com)
BASE_URL = "https://grupontsec.sysaidit.com"
USUARIO = "lucas.pacheco"
SENHA = "Chkp!234NTSEC02"

def criar_chamado_simples():
    # Criamos uma sessão para manter o login ativo entre as requisições
    session = requests.Session()

    # --- PASSO 1: LOGIN ---
    # O SysAid exige um POST para validar suas credenciais primeiro
    login_url = f"{BASE_URL}/api/v1/login"
    login_payload = {
        "user_name": USUARIO,
        "password": SENHA
    }

    try:
        print(f"Tentando login em: {login_url}...")
        response_auth = session.post(login_url, json=login_payload)

        if response_auth.status_code == 200:
            print("Login realizado com sucesso!")
            
            # --- PASSO 2: CRIAR O CHAMADO ---
            # O endpoint para Service Records (SR) é /api/v1/sr
            sr_url = f"{BASE_URL}/api/v1/sr"
            
            # O SysAid espera os dados dentro de uma lista chamada 'info'
            novo_ticket = {
                "info": [
                    {"key": "title", "value": "Chamado de Teste via Script Python"},
                    {"key": "problem_desc", "value": "Este chamado foi criado para testar a integração da API."},
                    {"key": "status", "value": "1"},  # Geralmente '1' é o ID para status Novo
                    {"key": "urgency", "value": "2"}   # Exemplo de Urgência (pode variar no seu sistema)
                ]
            }

            response_create = session.post(sr_url, json=novo_ticket)

            if response_create.status_code == 201:
                id_gerado = response_create.json().get('id')
                print(f"Sucesso! Chamado criado no SysAid. ID: {id_gerado}")
            else:
                print(f"Erro ao criar chamado: {response_create.status_code}")
                print(response_create.text)
        else:
            print(f"Falha na autenticação: {response_auth.status_code}")
            print(response_auth.text)

    except Exception as e:
        print(f"Ocorreu um erro de conexão: {e}")

if __name__ == "__main__":
    criar_chamado_simples()