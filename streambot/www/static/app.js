// stuff for adding and removing widgets, this should connect to the backend and add the appropriate widgets to the page


// Wait for document to load 
$(document).ready(() => {
    console.log('Page Loaded')

    // get the list of widgets from the backend and add them to the page
    getWidgets().then((widgets) => {
        console.log('Active widgets:', widgets)
        widgets.forEach((widget) => {
            addWidget(widget)
        })
    })
});

function getWidgets() {
    return new Promise((resolve, reject) => {
        $.get('/widgets/active', (data) => {
            resolve(data)
        })
    })
}

function addWidget(name) {
    // load /widgets/{name} and add it to the page
    $.get(`/widget/${name}`, (html) => {
        $container = $('#widget-container')
        $widget = $('<div class="widget" id="' + name + '-widget"></div>').html(html)
        $container.append($widget)
    })
}

function removeWidget(name) {
    $widget = $('#' + name + '-widget')
    $widget.remove()
}