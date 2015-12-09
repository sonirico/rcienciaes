{% if audio %}
    {% if audio.get_type == "episode" %}
        {{audio.title}}, de
         {% if audio.podcast.twitter %}
            {{ audio.podcast.twitter }}
         {% else %}
            {{audio.podcast.name}}
         {% endif %}
    {% elif audio.tweet %}
        {{audio.tweet}}
    {% else %}
        Promo: {{audio.title}}
    {% endif %}
{% endif %}