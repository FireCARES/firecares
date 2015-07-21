'use strict';

(function() {
    angular.module('fireStation.departmentDetailController', [])

    .controller('jurisdictionController', function($scope, $http, FireStation, map) {
          var departmentMap = map.initMap('map', {scrollWheelZoom: false});
          var showStations = true;
          var stationIcon = L.FireCARESMarkers.firestationmarker();
          var headquartersIcon = L.FireCARESMarkers.headquartersmarker();
          var fitBoundsOptions = {};
          $scope.stations = [];
          var layersControl = L.control.layers().addTo(departmentMap);

          if (showStations) {
              FireStation.query({department: config.id}).$promise.then(function(data) {
                 $scope.stations = data.objects;

                  var stationMarkers = [];
                  for (var i = 0; i < $scope.stations.length; i++) {
                      var station = $scope.stations[i];
                      var marker = L.marker(station.geom.coordinates.reverse(), {icon: stationIcon});
                      marker.bindPopup('<b>' + station.name + '</b><br/>' + station.address + ', ' + station.city + ' ' +
                          station.state);
                      stationMarkers.push(marker);
                  }

                  var stationLayer = L.featureGroup(stationMarkers);

                  // Uncomment to show Fire Stations by default
                  // stationLayer.addTo(departmentMap);

                  layersControl.addOverlay(stationLayer, 'Fire Stations');

                  if (config.geom === null) {
                    departmentMap.fitBounds(stationLayer.getBounds(), fitBoundsOptions);
                  }
              });
          }

          if (config.centroid != null) {
           var headquarters = L.marker(config.centroid, {icon: headquartersIcon});
           headquarters.addTo(departmentMap);
           layersControl.addOverlay(headquarters, 'Headquarters Location');
          };

          if (config.geom != null) {
           var countyBoundary = L.geoJson(config.geom, {
                                  style: function (feature) {
                                      return {color: '#0074D9', fillOpacity: .05, opacity:.8, weight:2};
                                  }
                              }).addTo(departmentMap);
            layersControl.addOverlay(countyBoundary, 'Jurisdiction Boundary');
            departmentMap.fitBounds(countyBoundary.getBounds(), fitBoundsOptions);
          } else {
              departmentMap.setView(config.centroid, 13);
          }
      })
})();
