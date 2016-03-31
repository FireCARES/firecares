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
          var heatmap = L.heatLayer([], {gradient: {0.55: '#74ac49', 0.65: '#febe00', 1: '#f6542f'}, radius: 5});
          var fires = L.featureGroup().addTo(departmentMap);
          var heatmapFilters = [];

          $scope.heatMapDataFilters = {};

          if (showStations) {
              FireStation.query({department: config.id}).$promise.then(function(data) {
                 $scope.stations = data.objects;

                  var stationMarkers = [];
                  var numFireStations = $scope.stations.length;
                  for (var i = 0; i < numFireStations; i++) {
                      var station = $scope.stations[i];
                      var marker = L.marker(station.geom.coordinates.reverse(), {icon: stationIcon});
                      marker.bindPopup('<b>' + station.name + '</b><br/>' + station.address + ', ' + station.city + ' ' +
                          station.state);
                      stationMarkers.push(marker);
                  }

                  if (numFireStations > 0) {
                      var stationLayer = L.featureGroup(stationMarkers);

                      // Uncomment to show Fire Stations by default
                      // stationLayer.addTo(departmentMap);

                      layersControl.addOverlay(stationLayer, 'Fire Stations');

                      if (config.geom === null) {
                      	departmentMap.fitBounds(stationLayer.getBounds(), fitBoundsOptions);
                      }
                  }
              });
          }

          if (config.centroid != null) {
            var headquarters = L.marker(config.centroid, {icon: headquartersIcon,zIndexOffset:1000});
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

          $scope.toggleFullScreenMap = function() {
              departmentMap.toggleFullscreen();
          };


          function processData(allText) {
            var allTextLines = allText.split(/\r\n|\n/);
            var headers = allTextLines[0].split(',');
            var lines = [];

            for (var i=1; i<allTextLines.length; i++) {
                var data = allTextLines[i].split(',');
                if (data.length == headers.length) {

                    var tarr = {};
                    for (var j=0; j<headers.length; j++) {
                        tarr[headers[j]] = data[j];
                    }

                    lines.push(tarr);
                }
            }
            return lines
          }

          $scope.setHeatMapData = function() {

              // this won't work it duplicates the filters
              var latlngs = [].concat(
                  $scope.heatMapDataFilters['hours'].top(Infinity),
                  $scope.heatMapDataFilters['days'].top(Infinity),
                  $scope.heatMapDataFilters['months'].top(Infinity));

              console.log('heatmap length', latlngs.length);
              console.log('heatmap data', $scope.heatMapDataFilters);
              heatmap.setLatLngs(latlngs.map(function (p) { return [p['y'], p['x']]; }));
              var portion = latlngs.length / $scope.heatmapData.size()
                  , n = (22 - departmentMap.getZoom()) / 22
                  , i = 17 * n * (portion / 2 + .5) + 3;
                heatmap.setOptions({
                    radius: i,
                    blur: 1.3 * (i - 2.99),
                    minOpacity: (1 - portion) * (1 - n) * .5
                });
          };


          layersControl.addOverlay(heatmap, 'Residential Fire Heatmap');

          departmentMap.on('overlayadd', function(layer) {
             if ( layer._leaflet_id === heatmap._leaflet_id && !$scope.heatmapData) {
                 departmentMap.spin(true);
                 $http.get('https://s3.amazonaws.com/firecares-test/fdny-fires.csv').then(function(response){
                   var lines = processData(response.data);
                   $scope.heatmapData = crossfilter(lines);
                   $scope.firesbyalarms = $scope.heatmapData.dimension(function(d) { return d.alarms; });
                   $scope.firesbyhour = $scope.heatmapData.dimension(function(d) { return new Date(d.alarm).getHours(); });
                   $scope.firesByDay = $scope.heatmapData.dimension(function(d) { return new Date(d.alarm).getDay(); });
                   $scope.firesByMonth = $scope.heatmapData.dimension(function(d) { return new Date(d.alarm).getMonth(); });

                   $scope.heatMapDataFilters['hours'] = $scope.firesbyhour;
                   $scope.heatMapDataFilters['days'] = $scope.firesByDay;
                   $scope.heatMapDataFilters['months'] = $scope.firesByMonth;

                   $scope.hours = $scope.firesbyhour.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                   $scope.days = $scope.firesByDay.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                   $scope.months = $scope.firesByMonth.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                   $scope.setHeatMapData(lines);
                   departmentMap.spin(false);
                 })
             }});
      });
})();
