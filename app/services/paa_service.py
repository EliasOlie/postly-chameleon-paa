from app.services.ai_service import generate_paa_data
from jinja2 import Template
from app.services.redis_service import cache_paa

HTML_TEMPLATE = """
<div class="postly-paa-container">
    
    <h3 class="postly-section-title">Perguntas Frequentes & Insights</h3>

    {# 1. Primeira Pergunta (Orgânica) #}
    {% if questions|length > 0 %}
    <details class="postly-paa-item">
        <summary class="postly-paa-question">{{ questions[0].q }}</summary>
        <div class="postly-paa-answer">{{ questions[0].a }}</div>
    </details>
    {% endif %}

    {# 2. O CARD NATIVO (Patrocínio IA) #}
    {% if ad %}
    <div class="postly-native-card">
        <div class="postly-card-header">
            <span class="postly-card-icon">💡</span>
            <h4 class="postly-card-title">{{ ad.title }}</h4>
        </div>
        <p class="postly-card-text">
            {{ ad.text }}
        </p>
        {# O link agora vem dinâmico da IA (ad.url) #}
        <a href="{{ ad.url }}" target="_blank" rel="sponsored noopener" class="postly-card-cta">
            {{ ad.cta_text }} ➜
        </a>
        <span class="postly-micro-label">Patrocinado</span>
    </div>
    {% endif %}

    {# 3. Restante das Perguntas #}
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
    Constrói apenas as perguntas orgânicas para o Google.
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
    ai_data = await generate_paa_data(content)
    
    questions = ai_data.get("questions", [])
    
    ad_content = ai_data.get("ad") if include_sponsored else None

    # 2. Renderiza HTML
    template = Template(HTML_TEMPLATE)
    html_output = template.render(
        questions=questions, 
        ad=ad_content 
    )
    
    json_ld_output = _build_json_ld(questions)
    
    return html_output, json_ld_output