
'use strict';

(function() {
    angular.module('fireStation.homeController', [])

    .controller('home', function($scope, map) {
      var homeMap = map.initMap('map', {scrollWheelZoom: false});
        homeMap.setView([40, -90], 4);
        var retina = L.Browser.retina ? '@2x': '';
        L.tileLayer('https://{s}.firecares.org/incidents/{z}/{x}/{y}'+ retina +'.png').addTo(homeMap);
    });
})();

