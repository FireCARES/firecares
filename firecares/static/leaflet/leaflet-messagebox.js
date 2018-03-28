L.Control.Messagebox = L.Control.extend({
    options: {
        position: 'topright',
        timeout: 7000,
    },

    onAdd: function (map) {
        this._container = L.DomUtil.create('div', 'leaflet-control-messagebox');


        L.DomEvent.on(this._container, 'click', this.hide, this);
        return this._container;
    },

    show: function (message, timeout) {
        var elem = this._container;
        elem.innerHTML = message;
        elem.style.display = 'block';

        timeout = timeout || this.options.timeout;

        if (typeof this.timeoutID == 'number') {
            clearTimeout(this.timeoutID);
        }
        this.timeoutID = setTimeout(function () {
            elem.style.display = 'none';
        }, timeout);
    },

    showforever: function (message, timeout) {
        var elem = this._container;
        elem.innerHTML = message + '    <i style="cursor:pointer;padding-left:4px;" class="fa fa-times-circle"></i>';
        elem.style.display = 'block';
        elem.style.border = "3px solid #ccc";
    },

    hide: function () {
        var elem = this._container;
        elem.style.display = 'none';
    }
});

L.Map.mergeOptions({
    messagebox: false
});

L.Map.addInitHook(function () {
    if (this.options.messagebox) {
        this.messagebox = new L.Control.Messagebox();
        this.addControl(this.messagebox);
    }
});

L.control.messagebox = function (options) {
    return new L.Control.Messagebox(options);
};
