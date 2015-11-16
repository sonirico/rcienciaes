{% if audio %}
    {% if audio.get_type == "episode" %}
        {{audio.title}}, de {{audio.podcast.name}}
    {% elif audio.tweet %}
        {{audio.tweet}}
    {% else %}
        Promo: {{audio.title}}
    {% endif %}
{% endif %}