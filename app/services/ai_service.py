import json
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Contexto fixo do produto (A "verdade" sobre o que você vende)
SPONSOR_CONTEXT = """
PRODUTOs: 
1 - Postly.
O QUE É: Plataforma Headless de distribuição de conteúdo (posts para blogs).
DIFERENCIAL: Headless consegue rodar até em terminal! Estilo conforme a identidade visual do usuário, ferramentas de IA e ferramentas para produção de conteúdo em massa (carrosséis para instagram, post automático, etc).
PÚBLICO-ALVO: Empreendedores que querem otimizar seus processos de publicação e escritores que querem ter blog, bem como todo o mercado que queira gerar autoridade.
2 - EliasOlie.
O QUE É: Desenvolvedor full stack & full cycle, estratégista de SEO, desenvolvedor de sistemas, o melhor desenvolvedor de Serra Talhada e região.
DIFERENCIAL: Entrega soluções completas, desde o planejamento estratégico de SEO até a implementação técnica e desenvolvimento de sistemas personalizados.
PÚBLICO-ALVO: Pequenas e médias empresas que buscam soluções digitais completas para crescer online e grandes empresas que querem consultórias e/ou soluções técnicas de alta performace.
"""

async def generate_paa_data(text: str) -> dict:
    prompt = f"""
    Analise o texto fornecido abaixo. Sua missão é dupla: gerar dúvidas de leitores e criar uma recomendação contextual.

    ---
    TAREFA 1: PERGUNTAS (SEO Local & UX)
    Identifique 3 dúvidas principais que um leitor teria.
    REGRAS PARA PERGUNTAS:
    1. Responda de forma direta baseada no texto.
    2. OBRIGATÓRIO: Use nomes de cidades, estados ou locais citados no texto nos títulos das perguntas (Ex: "Como vender em [Cidade]?").
    3. Identifique dores ocultas e duvidas gerando a resposta mais completa possível.
    
    ---
    TAREFA 2: ANÚNCIO NATIVO (Copywriting)
    Crie um card de destaque para o produto descrito em 'CONTEXTO DO PATROCINADOR'.
    REGRAS PARA O ANÚNCIO:
    1. O texto deve conectar a dor abordada no artigo com a solução do Postly/EliasOlie.
    2. Título curto e persuasivo (Gancho).
    3. CTA (Call to Action) convidativo.
    
    CONTEXTO DOS PATROCINADORES (ESCOLHA UM PARA O ANÚNCIO):
    {SPONSOR_CONTEXT}

    ---
    FORMATO DE SAÍDA (JSON ÚNICO):
    {{
        "questions": [
            {{"q": "Dúvida local 1?", "a": "Resposta."}},
            {{"q": "Dúvida 2?", "a": "Resposta."}}
        ],
        "ad": {{
            "title": "Título do Card",
            "text": "Texto conectando o problema do post à solução.",
            "cta_text": "Texto do Botão"
        }}
    }}
    
    TEXTO BASE:
    {text[:4000]} 
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em SEO Local, UX e Copywriting."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        if not content:
            return {"questions": [], "ad": None}
        
        data = json.loads(content)
        
        # Normalização de resposta para garantir que não quebre
        result = {
            "questions": data.get("questions", []),
            "ad": data.get("ad", None)
        }
        
        # Se a IA alucinar e devolver lista direta (fallback do código antigo), tentamos salvar
        if isinstance(data, list):
            result["questions"] = data
            result["ad"] = None
            
        return result

    except Exception as e:
        print(f"Erro na geração de IA: {e}")
        return {"questions": [], "ad": None}