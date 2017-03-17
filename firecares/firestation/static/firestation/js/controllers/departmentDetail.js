'use strict';

(function() {
    angular.module('fireStation.departmentDetailController', [])
        .controller('jurisdictionController', JurisdictionController)
        .filter('riskLevel', function() {
          return function(input, default_value) {
            input = input || '';
            switch (input) {
              case 1:
                return 'low';
              case 2:
              case 3:
                return 'medium';
              case 4:
                return 'high';
              default:
                return default_value || '';
            }
          };
        })
        .filter('grade', function() {
          return function(input, default_value) {
            input = input || '';
            switch (input) {
              case 1:
                return 'good';
              case 2:
              case 3:
                return 'fair';
              case 4:
                return 'poor';
              default:
                return default_value || '';
            }
          }
        })
        .directive('selectedRisk', function() {
          return {
            restrict: 'E',
            scope: {
              level: '='
            },
            template: '<span ng-if="level !== \'all\'" class="selected-risk">&nbsp;{{ level }} Risk</span>',
          }
        })
    ;

    JurisdictionController.$inject = ['$scope', '$timeout', '$http', 'FireStation', 'map', 'heatmap', '$filter', 'FireDepartment', '$analytics'];

    function JurisdictionController($scope, $timeout, $http, FireStation, map, heatmap, $filter, FireDepartment, $analytics) {
        var departmentMap = map.initMap('map', {scrollWheelZoom: false});
        var showStations = true;
        var stationIcon = L.FireCARESMarkers.firestationmarker();
        var headquartersIcon = L.FireCARESMarkers.headquartersmarker();
        var fitBoundsOptions = {};
        var countyBoundary = null;
        var eventCategory = 'department detail';
        $scope.metrics = window.metrics;
        $scope.urls = window.urls;
        $scope.level = window.level;
        $scope.messages = [];
        $scope.stations = [];
        $scope.residential_structure_fire_counts = _.isUndefined(window.metrics) ? '' : window.metrics.residential_structure_fire_counts;
        $scope.uploadBoundary = false;
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
            countyBoundary = L.geoJson(config.geom, {
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

                layersControl.addOverlay(heatmap.layer, 'Fires Heatmap');
                departmentMap.on('overlayadd', function(layer) {
                    if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
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
                    if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
                        showHeatmapCharts(false);
                    }
                });

                function showHeatmapCharts(show) {
                    $timeout(function() {
                        $scope.showHeatmapCharts = show;
                    });
                }
            });

        //
        // Parcels
        //
        var previousParcels = {};
        // Declare variables to avoid reallocating.
        var filter_iterator = 0;
        var joined_coordinate = '';

        // join coordinates on string to check if already added
        var join_coordinates = function(feature) {
          joined_coordinate = '';
          feature.forEach(function(currentValue) {
            joined_coordinate += currentValue.x + currentValue.y;
          });
          return joined_coordinate;
        };
        var parcels = new L.TileLayer.MVTSource({
          url: "https://{s}.firecares.org/parcels/{z}/{x}/{y}.pbf",
          debug: false,
          clickableLayers: null,
          mutexToggle: true,
          maxZoom: 18,
          minZoom: 15,

          getIDForLayerFeature: function(feature) {
            return feature.properties.parcel_id;
          },

          style: function(feature) {
            // If overlapping parcel then make it transparent.
            var current_coordinates = join_coordinates(feature.coordinates[0])
            if (current_coordinates in previousParcels) {
              return {
                color: 'rgba(0,0,0,0)'
              }
            } else {
              previousParcels[current_coordinates] = null;
            }

            var style = {};
            var selected = style.selected = {};
            var pointRadius = 1;

            function ScaleDependentPointRadius(zoom) {
              //Set point radius based on zoom
              var pointRadius = 1;
              if (zoom >= 0 && zoom <= 7) {
                pointRadius = 1;
              }
              else if (zoom > 7 && zoom <= 10) {
                pointRadius = 2;
              }
              else if (zoom > 10) {
                pointRadius = 3;
              }

              return pointRadius;
            }

            var type = feature.type;
            switch (type) {
              case 1: //'Point'
                // unselected
                style.color = CICO_LAYERS[feature.properties.type].color || '#3086AB';
                style.radius = ScaleDependentPointRadius;
                // selected
                style.selected = {
                  color: 'rgba(255,255,0,0.5)',
                  radius: 6
                };
                break;
              case 2: //'LineString'
                // unselected
                style.color = 'rgba(161,217,155,0.8)';
                style.size = 3;
                // selected
                style.selected = {
                  color: 'rgba(255,255,0,0.5)',
                  size: 6
                };
                break;
              case 3: //'Polygon'
                // unselected
                switch (feature.properties.risk_category) {
                  case 'Low':
                    style.color = 'rgba(50%,100%,50%,0.2)';
                    break;
                  case 'Medium':
                    style.color = 'rgba(100%,75%,50%,0.2)';
                    break;
                  case 'High':
                    style.color = 'rgba(100%,50%,50%,0.2)';
                    break;
                  default:
                    style.color = 'rgba(50%,50%,50%,0.2)';
                    break;
                }

                style.outline = {
                  color: 'rgb(20,20,20)',
                  size: 1
                };
                // selected
                style.selected = {
                  color: 'rgba(255,255,0,0.5)',
                  outline: {
                    color: '#d9534f',
                    size: 3
                  }
                };
            }

            return style;
          },

          onClick: function(evt) {
            if (config.showParcels) {
              var message = 'No parcel data found at this location.';
              if (evt.feature != null) {
                  message = '';

                  var items = {
                      'Address': 'addr',
                      'City': 'city',
                      'State': 'state',
                      'Zip': 'zip',
                      'Building Sq Footage': 'bld_sq_ft',
                      'Stories': 'story_nbr',
                      'Units': 'units_nbr',
                      'Condition': 'condition',
                      'Year Built': 'yr_blt',
                      'Rooms': 'rooms',
                      'Bed Rooms': 'bed_rooms',
                      'Total Value': 'tot_val',
                      'Land Value': 'lan_val',
                      'Improvements Value': 'imp_val',
                      'Structure Hazard Risk Level': 'risk_category'
                  };

                  _.each(_.pairs(items), function(pair){
                      var key = pair[0];
                      var value = evt.feature.properties[pair[1]];

                      if (key.indexOf('Value') !== -1 && value != null) {
                          value = $filter('currency')(value, '$', 0);
                      }

                      if ((key === 'Building Sq Footage' || key === 'Units') && value != null) {
                          value = $filter('number')(value, 0);
                      }

                      value = value ? value : 'Unknown';
                      message += '<b>' + key + ':</b> ' + value + '</br>';
                  });

                  L.popup()
                      .setLatLng(evt.latlng)
                      .setContent(message)
                      .openOn(departmentMap);

              }
            }
          }
        });
        layersControl.addOverlay(parcels, 'Parcels');

        $scope.shp = null;

        $scope.toggleBoundary = function() {
          if (!$scope.shp) {
            angular.element("input[name='newBoundary']").click();
          }
        };

        $scope.processBoundaryShapefile = function(file) {
          var fr = new FileReader();
          fr.onload = function(f) {
            var content = f.currentTarget.result;
            // No perceived error event, so resort to timeout
            var to = $timeout(function() {
              $scope.messages = [];
              $scope.messages.push({class: 'alert-danger', text: 'Shapefile appears to be invalid or unparseable, please ensure your target file is a .zip file with the mandatory .shp, .dbf and .shx files and re-upload.  If there is a .shp.xml file in the zipped bundle, removing that file from the bundle could help.'})
            }, 2000);
            var shp = new L.Shapefile(content).on('data:loaded', function(e) {
              $scope.$apply(function() {
                $timeout.cancel(to);
                $scope.messages = [];
                $scope.shp = e.target;
                $scope.shp.addTo(departmentMap);
                departmentMap.fitBounds($scope.shp);
              });
            });
          };
          fr.readAsArrayBuffer(file);
        };

        $scope.commitBoundary = function() {
          var features = $scope.shp.getLayers()[0].toGeoJSON();
          // Force multipolygon
          if (features.geometry.type === "Polygon") {
            features.geometry.coordinates = [features.geometry.coordinates];
            features.geometry.type = "MultiPolygon";
          }
          var fd = new FireDepartment({
            id: config.id,
            geom: features.geometry
          });
          fd.$update().then(function() {
            // Remove old jurisdiction boundary
            if (countyBoundary) {
              departmentMap.removeLayer(countyBoundary);
              layersControl.removeLayer(countyBoundary);
            }
            countyBoundary = $scope.shp;
            countyBoundary.setStyle({color: '#0074D9', fillOpacity: .05, opacity: .8, weight: 2});
            layersControl.addOverlay(countyBoundary, 'Jurisdiction Boundary');
            $scope.shp = null;
            $scope.messages = [];
            $scope.messages.push({class: 'alert-success', text: 'Department jurisdiction boundary updated.'});
          }, function() {
            $scope.messages.push({class: 'alert-danger', text: 'Server issue updating jurisdiction boundary.'});
          });
        };

        $scope.cancelBoundary = function() {
          departmentMap.removeLayer($scope.shp);
          $scope.shp = null;
          angular.element("form[name='boundaryUpload']").get(0).reset();
        };

        $scope.setLevel = function(level) {
          $analytics.eventTrack('change risk level', {
            category: eventCategory,
            label: level
          });
          $scope.level = level;
        };

        departmentMap.on('overlayadd', function(layer) {
          $analytics.eventTrack('enable layer', {
            category: eventCategory + ': map',
             label: layer.name
           });
        });

        departmentMap.on('overlayremove', function(layer) {
          $analytics.eventTrack('disable layer', {
            category: eventCategory + ': map',
            label: layer.name
          });
        });

        departmentMap.on('fullscreenchange', function(e) {
          status = e.target.isFullscreen() ? 'enable' : 'disable';
          $analytics.eventTrack(status + ' full screen', {
            category: eventCategory + ': map'
          });
        });

        function heatMapFiltered(e) {
          $analytics.eventTrack('filter heat map', {
            category: eventCategory + ': map',
            label: 'filter type: ' + e.filterType + ', filter: ' + e.filter
          });
        }

        departmentMap.on('heatmapfilterchanged',
          _.throttle(heatMapFiltered, 500, {trailing: true}))

        $timeout(function() {
          angular.element(".loading").fadeOut();
        }, 0);
    }
})();
