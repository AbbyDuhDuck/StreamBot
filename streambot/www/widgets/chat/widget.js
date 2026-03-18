
const TWITCH_EMOTE = (emote) => `<img class="twitch-emote emote"
srcset="
//static-cdn.jtvnw.net/emoticons/v2/${emote}/default/dark/1.0 1x, 
//static-cdn.jtvnw.net/emoticons/v2/${emote}/default/dark/2.0 2x, 
//static-cdn.jtvnw.net/emoticons/v2/${emote}/default/dark/4.0 4x, 
"
loading="lazy" decoding="async">`;
const YOUTUBE_EMOTE = (emote) => `<img class="youtube-emote emote"
src="${emote}"
loading="lazy" decoding="async">`;



function parseEmotes(data) {
    msg = data.message;
    emote_fmt = (emote) => '';
    // -=-=- //
    if (data.platform == 'twitch') emote_fmt = TWITCH_EMOTE;
    if (data.platform == 'youtube') emote_fmt = YOUTUBE_EMOTE;
    // -=-=- //
    for (const emote in data.emotes) {
        const html = emote_fmt(data.emotes[emote])
        msg = msg.split(emote).join(html);
    }
    return msg
}

function addMessageHTML(html) {
    // console.log("Adding message HTML:", html)
    $container = $('#message-container')
    $container.append(html)

    $container.animate({
        scrollTop: $container.prop('scrollHeight')
    }, 1000);
}


// Wait for document to load 
$(document).ready(() => { 

    $('.raw-emotes').each(function() {
        $this = $(this)
        const text = $this.text();
        const emotes = JSON.parse($this.attr('emotes'));
        const platform = $this.attr('platform');

        console.log(platform, text, emotes);

        html = parseEmotes({
            message: text,
            emotes: emotes,
            platform: platform,
        })
        $this.html(html)
        $this.removeClass('raw-emotes');
    });
    
    // Connect to the WebSocket server
    const ws = new WebSocket("ws://127.0.0.1:13337/ws/chat");
    
    ws.addEventListener("open", () => {
        console.log("Connected to chat WebSocket");

        $.get("/widget/chat/notification/", {message:"Chat Connected"}, (html) => {
            addMessageHTML(html)
        })
    });
    
    // Listen for stop time updates from Python
    ws.addEventListener("message", (event) => {
        try {
            const data = JSON.parse(event.data);
            // console.log("Received message from WebSocket:", data);
            if (data.event === "chat-message") {
                data.message.message = parseEmotes(data.message)
                // send a get to widgets/chat/message with the message data as query params
                $.get("/widget/chat/message/", data.message, (html) => {
                    addMessageHTML(html)
                })
            }
            if (data.event === "chat-notification") {
                $.get("/widget/chat/notification/", data.message, (html) => {
                    addMessageHTML(html)
                })
            }
        } catch (err) {
            console.error("Failed to parse WS message:", err);
        }
    });
    
    ws.addEventListener("close", () => {
        console.log("WebSocket disconnected");
    });
    

    $('#message-input').keypress((e) => { 
        // Enter key corresponds to number 13 
        if (e.which === 13) {
            const $input = $('#message-input')
            const input = $input.val()

            if (input == '') return

            $input.val('')
            const id = new Date().valueOf()

            console.log('webui', input); 

            ws.send(JSON.stringify({
                event: 'message',
                data: {message:input, id}
            }));
        }
    }) 
}); 
