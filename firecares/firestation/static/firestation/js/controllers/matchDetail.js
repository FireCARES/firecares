'use strict';

(function() {
    angular.module('fireStation.matchDetailController', [])

    .controller('matchController', function($scope, $http, FireStation, map) {
    
    var departmentMap = map.initMap('map', {scrollWheelZoom: false});
    var fitBoundsOptions = {};
    var layersControl = L.control.layers().addTo(departmentMap);
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    })
})();
