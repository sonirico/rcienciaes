// Player's states
var states = {
    'play' : 'Sounding ...',
    'stop' : 'Stopped',
    'pause' : 'Paused'
};
// actions: asoc array which associates actions to functions
var actions = {
    'play' : 'play_player()',
    'stop' : 'stop_player()',
    'pause' : 'pause_player()'
};

function play_player()
{
    $('#time_current_song').show();
    $('#status').show();
    //Mejorar esto
    $('#play').removeAttr('src').attr('src', button_images['played']);
    $('#stop').removeAttr('src').attr('src', button_images['stop']);
    $('#pause').removeAttr('src').attr('src', button_images['pause']);
}

function pause_player()
{
    $('#time_current_song').show();
    $('#status').show();
    //Mejorar esto
    $('#play').removeAttr('src').attr('src', button_images['play']);
    $('#stop').removeAttr('src').attr('src', button_images['stop']);
    $('#pause').removeAttr('src').attr('src', button_images['paused']);
}


function stop_player()
{
    $('#progressbar').val(0);
    $('#time_current_song').hide();
    $('#status').hide();
    //Mejorar esto
    // button_images: associative array preloaded in templates/index.html
    $('#stop').removeAttr('src').attr('src', button_images['stopped']);
    $('#play').removeAttr('src').attr('src', button_images['play']);
    $('#pause').removeAttr('src').attr('src', button_images['pause']);
}

$('document').ready(function(){
    current_sound_file();
    $('#back-top').fadeOut();

});


$(window).scroll(function(){
    if ($(this).scrollTop() > 300 )
    {
        $('#back-top').fadeIn();
    }
    else{
        $('#back-top').fadeOut();
    }
})

$(function button_clicked () {
    $(document).ready(function() {
        $('.action_button').click(function() {
            act = $(this).attr('id');
            /* Call the associate function when an action is performed */
            jQuery.globalEval(actions[act]);
            $.ajax({
                type: 'GET',
                url: 'mpd_action/' + act,
                dataType: 'html',
            });
        });
    });
});

$(function mini_button_clicked (){
    $(document).ready(function() {
        stop_player();
        $('div[id ^= audio-]').click(function() {
            jQuery.globalEval(actions['stop']);

            audio_id=$(this).attr('id');
            audio_id=audio_id.substring(6,audio_id.length);
            $.ajax({
                type: 'GET',
                url: 'mpd_action_playsong/' + audio_id,
                dataType: 'html',
            })
        });
    })
})

/* Función que descarga las covers de la playlist */
$(function (){
    var id_decorator = 'div_cover_'
    $('div[id ^= ' + id_decorator + ']').each(function(i){
        div_id = $(this).attr('id');
        div_id = div_id.substring(id_decorator.length, div_id.length);
        $('#img_' + div_id).removeAttr('src').attr('src', COVERS_DIR + $('#cover_' + div_id).val());
    /*
        $.ajax({
            type: 'POST',
            url: 'get_cover/',
            data: {'filename': $('#input_cover_' + div_id).val(), 'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val() },
            dataType: 'text',
            success: function(image_name)
            {

            }
        })
    */
    })
});

/* Hace scroll clicando en status hasta el lugar de la playlist correspondiente */
$(function (){
    $('#status').click(function(){
        if (current_pitch < 0) return;
        $('html,body').animate(
            {
                scrollTop: $("#tr_" + current_pitch).offset().top
            },
            'slow'
        );
    });
    $('#back-top').click(function(){
        $('html, body').stop().animate({
            scrollTop: $('body').offset().top
        }, 1000);
    });
})

/* Rebobina el audio en funcion de donde cliquemos la barra de progreso. */
$(function (){
    $('#progressbar').click(function(e){
        xAxis = parseInt(e.pageX -  $(this).position().left);
        width = parseInt($(this).width());
        percent = parseInt(xAxis * 100 / width);
        jQuery.ajax({
            type: 'GET',
            url: 'mpd_rewfor/' + percent,
            dataTpe: 'text',
            success: function(response)
            {
                //Actualizar datos
                //current_sound_file();
            }
        });
    });
});

/*Transforma segundos a formato H:m:i */
function format_time(seconds)
{
    if (! seconds ) return '';
    hours   = String(parseInt(seconds / 3600));
    minutes = String(parseInt(seconds / 60) % 60);
    seconds = String(parseInt(seconds % 60));
    str = '';
    str += hours <= 0 ? '' : hours + 'h ';
    str += (minutes.length == 1 ? '0' + minutes : minutes) + 'm ';
    str += (seconds.length == 1 ? '0' + seconds : seconds) + 's ';
    return str;
}

function current_sound_file() {
    $(document).ready(function() {
        var request = $.ajax({
            type: 'GET',
            url: 'mpd_status',
            dataType: 'json'
        });

        request.done(function(html, textStatus){
            posicion = parseInt(html.song);
            current_pitch = posicion
            //Actualizamos el estado del boton nada mas empezar
            current_status = html.state;
            jQuery.globalEval(actions[current_status]);
            song_row = jQuery('tr.tr_audio:eq(' + posicion + ')');
            artist = jQuery('tr.tr_audio:eq(' + posicion + ') > td:eq(2)');
            song_name = jQuery('tr.tr_audio:eq(' + posicion + ') > td:eq(3)');
            song_row.addClass('active');
            for (var i = 0; i < jQuery('tr.tr_audio').length; i++)
            {
                if (i != posicion)
                {
                    row = jQuery('tr.tr_audio:eq(' + i + ')');
                    if (row.hasClass('active'))
                    {
                        row.removeClass('active');
                    }
                }
            }
            /*barra de progreso*/
            if (html.state == 'play')
            {
                tiempos = html.time;
                tiempos = tiempos.split(':');
                progreso = ( tiempos[0] / tiempos[1] ) * 100;
                $('#progressbar').attr('value', progreso);
            }
            var request = $.ajax({
                type: 'GET',
                url: '/admin/player/mpd_status',
                dataType: 'json'
            });

            request.done(function(html, textStatus){
                tiempos = html.time.split(':');
                progreso = ( tiempos[0] / tiempos[1] ) * 100;
                $('#progressbar').attr('value', progreso);
                $('#time_current_song').text(format_time(tiempos[0]))
                $('#status').text(states[html.state]);
            });

            /* Obtenemos los datos de la musica pausada*/
            var request = $.ajax({
                type: 'GET',
                url: '/api/podcast/',
                dataType: 'json'
            });

            request.done(function(html, textStatus){
                $('#strong_podcast').text(html.podcast_name);
                $('#strong_episode').text(html.episode_title);
                $('#strong_pitch').text(current_pitch + 1);
            });
            //timer = setTimeout('current_sound_file()', 1000);
        });
        timer = setTimeout('current_sound_file()', 1000);
    })
}//End current_sound_file()
