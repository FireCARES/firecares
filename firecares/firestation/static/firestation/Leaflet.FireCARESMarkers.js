(function () {
  "use strict";
  L.FireCARESMarkers = {};

  L.FireCARESMarkers.Icon = L.Icon.extend({
    options: {
      iconSize: [30,70],
      popupAnchor: [0,-30],
      shadowAnchor: null,
      shadowSize: null,
      shadowUrl: null
    }
  });

  L.FireCARESMarkers.icon = function(options) {
    return new L.FireCARESMarkers.Icon(options);
  };

  L.FireCARESMarkers.firestationmarker = function(options) {
     var defaultOptions = {iconUrl:'/static/firestation/fire-station.png',
                           iconRetinaUrl: '/static/firestation/fire-station@2x.png'};
     return new L.FireCARESMarkers.Icon(L.extend(defaultOptions, options));
  };

  L.FireCARESMarkers.headquartersmarker = function(options) {
     var defaultOptions = {iconUrl:'/static/firestation/headquarters.png',
                           iconRetinaUrl: '/static/firestation/headquarters@2x.png'};
     return new L.FireCARESMarkers.Icon(L.extend(defaultOptions, options));
  };

})();
