
'use strict';

(function() {
    angular.module('fireStation.homeController', [])

    .controller('home', function($scope, map, $filter) {
            var homeMap = map.initMap('map', {scrollWheelZoom: false});
            homeMap.setView([40, -90], 4);
            var headquartersIcon = L.FireCARESMarkers.headquartersmarker();

            if (featured_departments != null) {
                L.geoJson(featured_departments, {
                    pointToLayer: function(feature, latlng) {
                       return L.marker(latlng, {icon: headquartersIcon});
                    },
                    onEachFeature: function(feature, layer) {
                       if (feature.properties && feature.properties.name) {
                           var popUp = '<b><a href="' + feature.properties.url +'">' + feature.properties.name + '</a></b>';

                           if (feature.properties.dist_model_score != null) {
                             popUp += '<br><b>Performance score: </b> ' + feature.properties.dist_model_score + ' seconds';
                           }

                           if (feature.properties.predicted_fires != null) {
                             popUp += '<br><b>Predicted annual residential fires: </b> ' + $filter('number')(feature.properties.predicted_fires, 0);
                           }

                           layer.bindPopup(popUp);
                          }
                        }
                }).addTo(homeMap);
            }
        });
})();

