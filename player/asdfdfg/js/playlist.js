var timer = null;
var last_state = "";
var last_played_song_pos = -1;
var states = {
    'play' : 'Sounding',
    'stop' : 'Stopped',
    'pause' : 'Paused'
};

var gif = new BootstrapGif();

function BootstrapGif (){

    this.down = '<span id="volDown" class="gifIcon glyphicon glyphicon-volume-down" ></span>';
    this.up = '<span id="volUp" class="gifIcon glyphicon glyphicon-volume-up"></span>';
    this.initialized = false;

    this.init = function(){
        jQuery('#volDown').hide();
    }

    this.run = function(){
        //if (this.initialized)
            jQuery('.gifIcon').toggle();
    }

    this.wrapper = function(){
        return '<div class="gif" >' + this.down + this.up + '</div>';
    }

    this.replace = function($tr){
        jQuery('.gif').remove();
        if ( $tr != null )
            $tr.children().first().append(this.wrapper());
        this.init();
        //this.initialized = true;
    }

}

/*
    Format time
*/

function format_time(seconds){

    if (! seconds ) {
        return 'Duration not available';
    } else {
        var hours   = String(parseInt(seconds / 3600));
        var minutes = String(parseInt(seconds / 60) % 60);
        var seconds = String(parseInt(seconds % 60));
        var str = '';
        str += hours <= 0 ? '' : hours + 'h ';
        str += (minutes.length == 1 ? '0' + minutes : minutes) + 'm ';
        str += (seconds.length == 1 ? '0' + seconds : seconds) + 's ';
        return str;
    }
}
/*
    Plugin to manage times
*/
(function( $ ){

    $.fn.formatTime = function(){

        return this.each(function(){

            $(this).text(format_time($(this).data('duration')));

        });
    };

    $.fn.setTotalTime = function(columnClassName, dataName){

        var total_time = 0;

        jQuery("." + columnClassName).each(function(k, v){
            total_time += parseInt($(this).data(dataName));
        });

        this.text(format_time(total_time));

        return this;
    };


}(jQuery));

/* Handles player buttons */

$(function () {

    $('.action-button').click(function() {
        action = $(this).data('action');
        /* Call the associate function when an action is performed */

        var $request = jQuery.ajax({
            type: 'GET',
            url: 'mpd_action/' + action,
        });

        $request.done(function(){
            //jQuery.globalEval(actions[act]);
            // Detener/ la animación de la barra
            if ( [ "pause", "stop" ].indexOf( action ) > -1 ){
                jQuery("#the-progress-bar").removeClass("active");
            }
            else{
                jQuery("#the-progress-bar").removeClass("active").addClass("active");
            }
        });
    });

});



/*
    Defines what to do when a little button 'play it' is clicked in the playlist
*/

$(function (){
    //stop_player();
    $('button.play-it').click(function() {

        //jQuery.globalEval(actions['stop']);

        audio_pos = $(this).data('audioPos');

        if (audio_pos != null){
            jQuery.ajax({
                type: 'GET',
                url: 'mpd_action_play_song/' + audio_pos,
            });
        }
    });
});

/* Rebobina el audio en funcion de donde cliquemos la barra de progreso. */
$(function (){
    $('.progress').click(function(e){
        length = parseInt($(this).css('width'));
        xAxis = parseInt(e.pageX - $(this).offset().left);
        percent = parseInt(( xAxis / length ) * 100);

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

function play(){
    console.log('play');

}

function pause(){
    console.log('pause');
}

function stop(){
    console.log('stop');
}

function next(){
    console.log('next');
}

function previous(){
    console.log('previous');
}



function core() {

    var request = $.ajax({
        type: 'GET',
        url: '/api/status/',
        dataType: 'json'
    });

    request.done(function(json, httpStatusCode){

        function_name = json.state + "()";

        // just makes sense when state has changed
        if ( last_state != json.state ) {
            jQuery("#playlist-status").text(states[json.state]);
        }

        if ( json.state == "play" ){
            times = json.time;
            times = times.split(':');
            progress = (( times[0] / times[1] ) * 100) + '%';
            // Cronometro
            $('#progress-text').text(format_time(times[0]));
            // Porcentaje de progreso
            $('#the-progress-bar').css({'width': progress});
            // "Gif"
            gif.run();
        }

        //console.log("Current: " + jsonCurrent.pos + " Last: " + last_played_song_pos);
        if ( json.song != last_played_song_pos ){
            jQuery('.info').removeClass('info');

            $tr = jQuery('#grid-basic tbody').find('[data-songId="' + json.song + '"]').each(function(k, v){
                $(this).addClass('info');
            });

            gif.replace($tr);

            last_played_song_pos = json.song;
        }

        last_state = json.state;
    });

    request.fail(function(jqXHR, textStatus){

    });

    timer = setTimeout(core, 1000);
}//End current_sound_file()



 /*
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
            /*barra de progreso
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

            /* Obtenemos los datos de la musica pausada
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
        */