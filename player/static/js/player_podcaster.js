// Player's states
var states = {
    'play' : 'Sounding ...',
    'stop' : 'Stopped',
    'pause' : 'Paused'
};
/* Checa si el podcaster sale sin hacer replay
window.onunload = replay;
window.onbeforeunload = replay;

function replay()
{
    jQuery.ajax({
        type: 'GET',
        url: 'mpd_action/play',
        dataType: 'html',
    });
}*/
/******************************************/


$('document').ready(function(){
    current_sound_file();
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
        });


        timer = setTimeout('current_sound_file()', 1000);
    })
}//End current_sound_file()


/* Codigo relativo al modo live */

var TABS = { 'FORM': 0, 'TWEET': 1, 'LIVE': 2};
var file_size = 0; // En MB
var MAX_FILESIZE = 2; //MB

//Añadimos la funcion para que chequee que la imagen no exceda el tamaño
/*
jQuery.validator.addMethod("isLight", function(value, element){
alert(element);alert(value);
    return this.optional(element) || file_size <= MAX_FILESIZE;
}, "La imagen es demasiado grande. 2MB como máximo.");
*/

$(document).ready(function(){

    var form = $("#form_live").show();

    form.steps({
        headerTag: "h3",
        bodyTag: "section",
        transitionEffect: "slideLeft",
        stepsOrientation: "vertical",
        onStepChanging: function (event, currentIndex, newIndex)
        {
            //if (currentIndex > newIndex) return true;


            // Needed in some cases if the user went back (clean up)
            if (currentIndex < newIndex){
                // To remove error styles
                form.find(".body:eq(" + newIndex + ") label.error").remove();
                form.find(".body:eq(" + newIndex + ") .error").removeClass("error");
            }
            form.validate().settings.ignore = ":disabled,:hidden";
            return form.valid();
        },
        onFinishing: function (event, currentIndex)
        {
            form.validate().settings.ignore = ":disabled";
            return form.valid();
        },
        onFinished: function (event, currentIndex)
        {
            form.submit();
        }
    }).validate({
        rules: {
            image_file : {
                extension : "jpg|jpeg|png|gif|svg|ico"
            },
            event_title : {
                required : true,
                minlength : 2
            },
            artists : {
                required : true,
                minlength : 2
            }
        },
        messages : {
            image_file: {
                extension : "Extensiones permitidas: jpg,jpeg,png,gif,svg,ico"
            },
            event_title : {
                required : "Se requiere un título para el evento",
                minlength : "Escribe algo de más de 2 caracteres, anda"
            },
            artists : {
                required : "Se requiere saber los artistas",
                minlength : "Escribe algo de más de 2 caracteres, anda"
            }
        }
    });

    // Asigna a la variable file_size el peso de la imagen cada vez que es cambiada
    $('#id_image_file').bind('change', function(){
        // No mayor de 2 MB
        //alert($(this).val())
        file_size = this.files[0].size / (1024 * 1024);
    });

    var mLength = $('#id_content').val().length;
    $('#chars').text(mLength);
    //Numero de caracteres
    $('#id_content').keyup(function(){
        var mLength = $(this).val().length;
        $('#chars').text(mLength);
        $('#tweet_status').text('');
        $('#tweet_status').removeClass();
    });

    $('#id_content').focus(function(){
        $('#tweet_status').text('');
        $('#tweet_status').removeClass();
    });

    $('#input_submiter').click(function(){
        var form_data = {
            'content': $('#id_content').val(),
            'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
        }
        var request = $.ajax({
            type: 'POST',
            url: '/admin/player/live/tweet/',
            dataType: 'json',
            data: form_data
        });

        request.done(function(html, textStatus){
            $tweet_status = $('#tweet_status');
            $tweet_status.text('¡Tweet enviado!');
            $tweet_status.addClass('right');
        });

        request.fail(function(){
            $tweet_status = $('#tweet_status');
            $tweet_status.text('Fallo al enviar. Inténtalo más tarde.');
            $tweet_status.addClass('wrong');
        });
    });

});//End ready
