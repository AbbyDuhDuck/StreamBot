// stuff for adding and removing widgets, this should connect to the backend and add the appropriate widgets to the page


// -=-=- Widgets -=-=- //

// Wait for document to load then load a widget
function onLoadWidget (widget, container) {
    return () => {
        console.log('Page Loaded')
        addWidget(widget, container)
    }
}

// Wait for document to load then load active
function onLoadWidgets (container) {
    return () => {
        console.log('Page Loaded')
        
        // get the list of widgets from the backend and add them to the page
        getActiveWidgets().then((widgets) => {
            console.log('Active widgets:', widgets)
            widgets.forEach((widget) => {
                addWidget(widget, container)
            })
        })
    }
}

function getActiveWidgets() {
    return new Promise((resolve, reject) => {
        $.get('/widgets/active', (data) => {
            resolve(data)
        })
    })
}

function getWidgets() {
    return new Promise((resolve, reject) => {
        $.get('/widgets', (data) => {
            resolve(data)
        })
    })
}

function addWidget(name, container) {
    // load /widgets/{name} and add it to the page
    $.get(`/widget/${name}`, (html) => {
        $container = $(container)
        $widget = $('<div class="widget" id="' + name.replace('/', '-') + '-widget"></div>').html(html)
        $container.append($widget)
    })
}

function removeWidget(name) {
    $widget = $('#' + name + '-widget')
    $widget.remove()
}


// -=-=- Dashboards -=-=- //

function onLoadDashboards (container) {
    return () => { loadDashboards(container) }
}

// Wait for document to load then load active
function loadDashboards (container) {
    // get the list of dashboards from the backend and add them to the page
    getWidgets().then((dashboards) => {
        console.log('Active dashboards:', dashboards)
        dashboards.forEach((dashboard) => {
            addDashboard(dashboard, container)
        })
    })
}

function addDashboard(name, container) {
    // load /widgets/{name}/dashboard and add it to the page
    $.get(`/widget/${name}/dashboard`, (html) => {
        $container = $(container)
        $dashboard = $('<div class="dashboard" id="' + name + '-dashboard"></div>').html(html)
        $container.append($dashboard)
    })
    .fail(function() {console.log(`${name} widget has no dashboard view, skipping.`);})
}

function removeDashboard(name) {
    $dashboard = $('#' + name + '-dashboard')
    $dashboard.remove()
}





// -=-=- Splitter Drag Logic -=-=- //

let isDragging = false;

$(document).ready(() => {
    const $splitter = $('#splitter');
    const $chat = $('#chat-panel');

    $splitter.on('mousedown', () => {
        isDragging = true;
        $('body').addClass('resizing');
    });

    $(document).on('mousemove', (e) => {
        if (!isDragging) return;

        const min = 150;
        const max = window.innerWidth * 0.7;

        let newWidth = e.clientX;

        if (newWidth < min) newWidth = min;
        if (newWidth > max) newWidth = max;

        $chat.css('width', newWidth + 'px');
    });

    $(document).on('mouseup', () => {
        if (!isDragging) return;

        isDragging = false;
        $('body').removeClass('resizing');

        // saveLayout();
    });
});

