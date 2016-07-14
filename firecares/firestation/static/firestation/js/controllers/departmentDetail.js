'use strict';

(function() {
    angular.module('fireStation.departmentDetailController', [])
        .controller('jurisdictionController', JurisdictionController)
    ;

    JurisdictionController.$inject = ['$scope', '$timeout', '$http', 'FireStation', 'map', 'heatmap', 'favorite'];

    function JurisdictionController($scope, $timeout, $http, FireStation, map, heatmap, favorite) {
        var departmentMap = map.initMap('map', {scrollWheelZoom: false});
        var showStations = true;
        var stationIcon = L.FireCARESMarkers.firestationmarker();
        var headquartersIcon = L.FireCARESMarkers.headquartersmarker();
        var fitBoundsOptions = {};
        $scope.stations = [];
        var layersControl = L.control.layers().addTo(departmentMap);
        var fires = L.featureGroup().addTo(departmentMap);

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
            var headquarters = L.marker(config.centroid, {icon: headquartersIcon, zIndexOffset: 1000});
            headquarters.addTo(departmentMap);
            layersControl.addOverlay(headquarters, 'Headquarters Location');
        }

        if (config.geom != null) {
            var countyBoundary = L.geoJson(config.geom, {
                style: function(feature) { return {color: '#0074D9', fillOpacity: .05, opacity: .8, weight: 2}; }
            }).addTo(departmentMap);
            layersControl.addOverlay(countyBoundary, 'Jurisdiction Boundary');
            departmentMap.fitBounds(countyBoundary.getBounds(), fitBoundsOptions);
        } else {
            departmentMap.setView(config.centroid, 13);
        }

        $scope.toggleFullScreenMap = function() {
            departmentMap.toggleFullscreen();
        };

        $scope.onFavorite = favorite.onFavorite;

        //
        // Heatmap
        //

        var heatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + config.id + '-building-fires.csv';
        $http.head(heatmapDataUrl)
            .then(function(response) {
                var contentLength = Number(response.headers('Content-Length'));

                // Don't show the heatmap layer option for a department with no heatmap data.
                // HACK: A department with no heatmap data will still return the table header for the empty data, which
                //       has a length of 45 bytes. Remember to change this value if the columns ever change in any way.
                if (contentLength <= 45) {
                    return;
                }

                heatmap.init(departmentMap);
                $scope.heatmap = heatmap;
                $scope.showHeatmapCharts = false;

                layersControl.addOverlay(heatmap.layer, 'Heatmap of Low Risk Fires');

                departmentMap.on('overlayadd', function(layer) {
                    if (layer._leaflet_id === heatmap.layer._leaflet_id) {
                        if (heatmap.heat) {
                            showHeatmapCharts(true);
                        } else {
                            departmentMap.spin(true);
                            heatmap.download(heatmapDataUrl)
                                .then(function() {
                                    showHeatmapCharts(true);
                                }, function(err) {
                                    alert(err.message);
                                    layersControl.removeLayer(heatmap.layer);
                                })
                                .finally(function() {
                                    departmentMap.spin(false);
                                })
                            ;
                        }
                    }
                });

                departmentMap.on('overlayremove', function(layer) {
                    if (layer._leaflet_id === heatmap.layer._leaflet_id) {
                        showHeatmapCharts(false);
                    }
                });

                function showHeatmapCharts(show) {
                    $timeout(function() {
                        $scope.showHeatmapCharts = show;
                    });
                }
            })
        ;
    }
})();
