



// Wait for document to load 
$(document).ready(() => { 
    
    // Connect to the WebSocket server
    const ws = new WebSocket("ws://127.0.0.1:13337/ws/chat");
    
    ws.addEventListener("open", () => {
        console.log("Connected to chat WebSocket");
    });
    
    // Listen for stop time updates from Python
    ws.addEventListener("message", (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log("Received message from WebSocket:", data);
    
            if (data.event === "chat-message") {
                console.log("Received chat message:", data.message);
                // send a get to widgets/chat/message with the message data as query params
                $.get("/widget/chat/message/", data.message, (html) => {
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
    
    // console.log('Page Loaded')
    
    // $('#user-input').on('submit', () => { 

    //     // prevents default behaviour 
    //     // Prevents event propagation 
    //     return false; 
    // });

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

            // const ws = new WebSocket("ws://localhost:8765");
            
            // send the message to the backend
            // do a post to an endpoint that any of the widgets can connect to for receiving messages
            // or maybe websockets, depents on how we are doing the messaging rn
        }
    }) 
}); 


function addMessageHTML(html) {
    console.log("Adding message HTML:", html)
    $container = $('#message-container')
    $container.append(html)

    $container.animate({
        scrollTop: $container.prop('scrollHeight')
    }, 1000);
}