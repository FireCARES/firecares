
'use strict';

(function() {
    angular.module('fireStation.homeController', [])

    .controller('home', function($scope, map, FireDepartment) {
            var homeMap = map.initMap('map', {scrollWheelZoom: false});
            homeMap.setView([40, -90], 4);


            FireDepartment.query({featured: true}).$promise.then(function(data) {
                for (i = 0; i < data.length; i++) {
                    L.marker([51.5, -0.09]).addTo(homeMap).bindPopup('A pretty CSS3 popup.<br> Easily customizable.');
                }
            });
        });
})();

