from app.services.ai_service import generate_paa_data
from jinja2 import Template
from app.services.redis_service import cache_paa
from app.config import settings

# Template Híbrido: Perguntas Fechadas + Card Aberto
HTML_TEMPLATE = """
<div class="postly-paa-container">
    
    {# Título opcional para dar contexto #}
    <h3 class="postly-section-title">Perguntas Frequentes & Insights</h3>

    {# 1. Primeira Pergunta (Orgânica) #}
    {% if questions|length > 0 %}
    <details class="postly-paa-item">
        <summary class="postly-paa-question">{{ questions[0].q }}</summary>
        <div class="postly-paa-answer">{{ questions[0].a }}</div>
    </details>
    {% endif %}

    {# 2. O CARD NATIVO (Patrocínio IA - Já vem aberto) #}
    {% if ad %}
    <div class="postly-native-card">
        <div class="postly-card-header">
            <span class="postly-card-icon">💡</span>
            <h4 class="postly-card-title">{{ ad.title }}</h4>
        </div>
        <p class="postly-card-text">
            {{ ad.text }}
        </p>
        <a href="{{ ad_link }}" target="_blank" rel="sponsored noopener" class="postly-card-cta">
            {{ ad.cta_text }} ➜
        </a>
        <span class="postly-micro-label">Patrocinado</span>
    </div>
    {% endif %}

    {# 3. Restante das Perguntas (Orgânicas) #}
    {% for item in questions[1:] %}
    <details class="postly-paa-item">
        <summary class="postly-paa-question">{{ item.q }}</summary>
        <div class="postly-paa-answer">{{ item.a }}</div>
    </details>
    {% endfor %}

</div>
"""

def _build_json_ld(items: list) -> dict:
    """
    Constrói apenas as perguntas orgânicas.
    Ignoramos o AD aqui para evitar penalidade de Schema Spam no Google.
    """
    main_entity = []
    
    for item in items:
        main_entity.append({
            "@type": "Question",
            "name": item['q'],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item['a']
            }
        })

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity
    }

@cache_paa(expire=60*60*24*7)
async def process_paa(content: str, include_sponsored: bool):
    # Chama a nova função de IA
    ai_data = await generate_paa_data(content)
    
    questions = ai_data.get("questions", [])
    ad_content = ai_data.get("ad")
    
    # Se o usuário desativou patrocinio ou a IA falhou em gerar o ad
    final_ad = ad_content if include_sponsored else None

    # Link padrão para onde o CTA vai levar (pode parametrizar no futuro)
    # Por segurança, o link é fixo, mas o texto é dinâmico da IA.
    target_link = "https://landing.eliasolie.com.br/contact"

    # Renderiza HTML
    template = Template(HTML_TEMPLATE)
    html_output = template.render(
        questions=questions,
        ad=final_ad,
        ad_link=target_link
    )
    
    # Constrói JSON-LD (Somente perguntas)
    json_ld_output = _build_json_ld(questions)
    
    return html_output, json_ld_output