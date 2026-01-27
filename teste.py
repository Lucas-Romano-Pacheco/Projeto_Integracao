import requests
import json

# --- CONFIGURACOES ---
# Certifique-se de usar a URL limpa (sem o #!/view/)
URL_ALVO = "http://127.0.0.1:5000/receber-jira" 

def testar_integracao_local():
    print("Iniciando teste de integracao...")

    # 1. DADO SIMULADO
    payload_jira = {
        "issue": {
            "fields": {
                "summary": "Chamado de Teste Lucas",
                "description": "Descricao enviada via Python"
            }
        }
    }

    # 2. MAPEAMENTO
    dados_formatados = {
        "info": [
            {"key": "title", "value": payload_jira['issue']['fields']['summary']},
            {"key": "problem_desc", "value": payload_jira['issue']['fields']['description']}
        ]
    }

    # 3. ENVIO
    # Usando a variavel correta: URL_ALVO
    print(f"Enviando dados para: {URL_ALVO}")
    
    try:
        response = requests.post(URL_ALVO, json=dados_formatados)
        if response.status_code == 200:
            print("Sucesso! O dado chegou ao Webhook.site.")
        else:
            print(f"Erro no envio. Status: {response.status_code}")
    except Exception as e:
        print(f"Erro de conexao: {e}")

if __name__ == "__main__":
    testar_integracao_local()