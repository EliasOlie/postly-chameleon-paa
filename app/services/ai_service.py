import json
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Contexto rico com URLs e critérios de escolha
SPONSOR_CONTEXT = """
OPÇÃO A: Postly (SaaS / Ferramenta)
- O QUE É: Headless CMS para blogs, focado em performance, IA e distribuição de conteúdo.
- QUANDO ESCOLHER: Se o texto fala sobre criar blog, automação, PAA, estratégia de conteúdo, SEO técnico DIY ou ferramentas.
- URL: https://postly.eliasolie.com.br

OPÇÃO B: EliasOlie (Serviço / Consultoria)
- O QUE É: Desenvolvedor Full Stack e Estrategista de SEO (O melhor de Serra Talhada).
- QUANDO ESCOLHER: Se o texto fala sobre contratar site, desenvolvimento de sistemas complexos, consultoria ou "eu faço para você".
- URL: https://landing.eliasolie.com.br/contact
"""

async def generate_paa_data(text: str) -> dict:
    prompt = f"""
    Analise o texto fornecido abaixo. Sua missão é atuar como um estrategista de SEO e Copywriter.

    ---
    ETAPA 1: SELEÇÃO DO PATROCINADOR
    Analise o tópico do texto. Qual das duas opções abaixo resolve melhor a dor do leitor?
    {SPONSOR_CONTEXT}

    ---
    ETAPA 2: GERAÇÃO DE PERGUNTAS (SEO Local)
    Gere 3 dúvidas principais baseadas no texto.
    
    REGRAS CRÍTICAS DE LOCALIZAÇÃO:
    1. Procure no texto o nome da cidade ou região (Ex: "Serra Talhada").
    2. Se encontrar, USE O NOME REAL no título da pergunta (Ex: "Como criar site em Serra Talhada?").
    3. SE NÃO ENCONTRAR CIDADE: NÃO use "[Cidade]" ou "[Estado]". Use termos como "na sua região" ou "para sua empresa". 
    4. PROIBIDO retornar placeholders com colchetes.

    ---
    ETAPA 3: CRIAÇÃO DO ANÚNCIO (Native Ad)
    Crie o conteúdo do card para o patrocinador ESCOLHIDO na Etapa 1.
    1. Título: Curto, impacto alto (System Alert style).
    2. Texto: Conecte a dor do artigo à solução escolhida.
    3. Link: Use a URL correta da opção escolhida.

    ---
    FORMATO DE SAÍDA (JSON VÁLIDO):
    {{
        "questions": [
            {{"q": "Pergunta 1 (com local real se houver)?", "a": "Resposta."}}
        ],
        "ad": {{
            "title": "Título do Card",
            "text": "Copy persuasiva.",
            "cta_text": "Texto do Botão (Ex: Conhecer o Postly / Falar com Elias)",
            "url": "A URL correta baseada na escolha"
        }}
    }}
    
    TEXTO BASE:
    {text[:4000]} 
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em SEO Local e Marketing de Conteúdo."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        if not content:
            return {"questions": [], "ad": None}
        
        data = json.loads(content)
        
        # Tratamento de erro caso a IA esqueça a chave URL
        if data.get("ad") and "url" not in data["ad"]:
            # Fallback seguro
            data["ad"]["url"] = "https://landing.eliasolie.com.br/contact"

        return {
            "questions": data.get("questions", []),
            "ad": data.get("ad", None)
        }

    except Exception as e:
        print(f"Erro na geração de IA: {e}")
        return {"questions": [], "ad": None}