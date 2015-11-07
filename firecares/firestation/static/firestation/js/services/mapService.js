'use strict';

(function() {
    angular.module('fireStation.mapService', [])

    .provider('map', function() {
        this.$get = function($rootScope) {
          return this;
        };

        this.addBaseLayers = function(map) {
            if (map==null) {
                return
            }

            var retina = L.Browser.retina ? '@2x': '';

            L.tileLayer('https://{s}.firecares.org/base/{z}/{x}/{y}' + retina + '.png',
              {'attribution': '© Mapbox', 'opacity':.95}).addTo(map);
        };

        this.initMap = function(div, options) {
            var defaultOptions = {
              boxZoom: true,
              zoom: 15,
              zoomControl: true,
              attributionControl: false,
              scrollWheelZoom: false,
              doubleClickZoom: false,
              fullscreenControl: false
          };

            angular.extend(defaultOptions, options);
            var map = L.map(div, options);
            this.addBaseLayers(map);
            return map;

        }
  });


})();
