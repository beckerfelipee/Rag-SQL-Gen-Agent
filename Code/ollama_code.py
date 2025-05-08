import getpass
import os
#from langchain.chat_models import ChatOllama
from typing import TypedDict, List
from langchain_community.chat_models import ChatOllama

# Definir a estrutura para saída estruturada
class MovieReview(TypedDict):
    movie_title: str
    year: int
    review: str
    rating: float
    recommended: bool

# Inicialize o modelo Llama3.2:3b via Ollama com suporte para saída estruturada
llm = ChatOllama(model="llama3.2:3b")

# Exemplo de uso com saída padrão
def test_model_basic():
    response = llm.invoke("Olá, como você está?")
    print("Resposta padrão:")
    print(response.content)

# Exemplo de uso com saída estruturada
def test_model_structured():
    # Cria uma instância separada com saída estruturada
    llm_structured = ChatOllama(
        model="llama3.2:3b",
        with_structured_output=True
    )
    
    # Faz uma pergunta que espera uma resposta estruturada
    prompt = "Faça uma análise do filme 'Matrix'. Inclua título, ano, análise, nota de 0 a 10 e se recomenda."
    
    # Invoca o modelo com a classe de saída especificada
    response = llm_structured.with_structured_output(MovieReview).invoke(prompt)
    
    print("\nResposta estruturada:")
    print(f"Título: {response.movie_title}")
    print(f"Ano: {response.year}")
    print(f"Análise: {response.review}")
    print(f"Nota: {response.rating}")
    print(f"Recomendado: {response.recommended}")

# Caso prefira definir uma variável de ambiente para configuração
# (opcional, já que Ollama roda localmente)
if os.environ.get("OLLAMA_HOST") is None:
    # Pode definir um host customizado se necessário, o padrão é http://localhost:11434
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"

# Se este arquivo for executado diretamente
if __name__ == "__main__":
    test_model_basic()
    test_model_structured()
