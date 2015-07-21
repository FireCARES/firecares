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

            L.tileLayer('https://{s}.tiles.mapbox.com/v3/garnertb.m9pm846a/{z}/{x}/{y}.png',
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
