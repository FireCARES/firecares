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
            template: '<span ng-if="level !== \'all\'" class="selected-risk">&nbsp;{{ level }} Hazard</span>',
          }
        })
    ;

    JurisdictionController.$inject = ['$scope', '$timeout', '$http', 'FireStation', 'map', 'heatmap', '$filter', 'FireDepartment', '$analytics', 'WeatherWarning', '$interpolate', 'FireStationandStaffing', 'ServiceAreaRollup', 'EfffChartRollup'];

    function JurisdictionController($scope, $timeout, $http, FireStation, map, heatmap, $filter, FireDepartment, $analytics, WeatherWarning, $interpolate, FireStationandStaffing, ServiceAreaRollup, EfffChartRollup) {
        var departmentMap = map.initMap('map', {scrollWheelZoom: false});
        var showStations = true;
        var stationIcon = L.FireCARESMarkers.firestationmarker();
        var headquartersIcon = L.FireCARESMarkers.headquartersmarker();
        var fitBoundsOptions = {};
        var countyBoundary = null;
        var eventCategory = 'department detail';
        
        var serviceArea,efffArea;
        var max = 8;
        var serviceAreaData = null;
        var efffAreaData = null;
        var mouseOverAddedOpacity = 0.25;    
        var highlightColor = 'blue';
        
        $scope.metrics = window.metrics;
        $scope.urls = window.urls;
        $scope.level = window.level;
        $scope.messages = [];
        $scope.weather_messages = [];
        $scope.stations = [];
        $scope.showServiceAreaChart = false;
        $scope.showEFFFChart = false;
        $scope.residential_structure_fire_counts = _.isUndefined(window.metrics) ? '' : window.metrics.residential_structure_fire_counts;
        $scope.parcel_hazard_level_counts = "";
        $scope.parcel_efff_counts = "";
        $scope.department_personnel_counts = " Personnel/Assets Available";
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
        
        //
        // Weather Warnings
        //
        WeatherWarning.query({department: config.id}).$promise.then(function(data) {

            var weatherPolygons = [];
            var numWarnings = data.objects.length;

            for (var i = 0; i < numWarnings; i++) {
              var warning = data.objects[i];
              var poly = L.multiPolygon(warning.warngeom.coordinates.map(function(d){return mapPolygon(d)}),{color: '#f00', weight:'1px'});
              var warningdate = new Date(warning.expiredate);
              poly.bindPopup('<b>' + warning.prod_type + '</b><br/>Ending: ' + warningdate.toDateString() +' '+ warningdate.toLocaleTimeString() + '<br/><br/><a target="_blank" href='+warning.url+'>Click for More Info</a>');
              weatherPolygons.push(poly);
              $scope.weather_messages.push({class: 'alert-warning', text: '<a class="alert-link" target="_blank" href='+warning.url+'>'+' ' + warning.prod_type + '  Until  ' + warningdate.toDateString() +',  '+ warningdate.toLocaleTimeString().replace(':00 ',' ') +'</a>'});
            }

            if (numWarnings > 0) {
              var weatherLayer = L.featureGroup(weatherPolygons);
              weatherLayer.addTo(departmentMap); //deafult on
              weatherLayer.bringToBack();
              layersControl.addOverlay(weatherLayer, 'Weather Warnings');

              // Hide layer when zoom gets to parcel layer z15
              departmentMap.on('zoomend', function() {
                if(departmentMap.hasLayer(weatherLayer)){
                  if(departmentMap.getZoom() > 14){
                    weatherLayer.eachLayer(function(layer){
                        layer.setStyle({fillOpacity :0});
                    });
                  }
                  else{
                    weatherLayer.eachLayer(function(layer){
                        layer.setStyle({fillOpacity :.2});
                    });
                  }
                }
              });
            }

            function mapPolygon(poly){
              return poly.map(function(line){return mapLineString(line)})
            }

            function mapLineString(line){
              return line.map(function(d){return [d[1],d[0]]})  
            }
        });

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
                //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
                if (contentLength <= 59) {
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
          minZoom: 10,

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

        //
        // Service Area
        //
        serviceArea = L.geoJson(null, {
          onEachFeature: function(feature, layer) {
              layer.bindPopup(feature.properties.Name + ' minutes');
              layer.on('mouseover', function(e) {
                 layer.setStyle({fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5) + mouseOverAddedOpacity, fillColor: highlightColor});
              });
              layer.on('mouseout', function(e) {
                 layer.setStyle({weight: 0.8, fillOpacity:-(feature.properties.ToBreak * 0.8 - max) / (max * 1.5), fillColor: '#33cc33'});
              });
          }
        });

        layersControl.addOverlay(serviceArea, 'Service Area');

        efffArea = L.geoJson(null, {
          onEachFeature: function(feature, layer) {
              layer.bindPopup(feature.properties.Name + '<br>'+ feature.properties.ToBreak);
              layer.on('mouseover', function(e) {
                 layer.setStyle({weight: 1,fillOpacity: .9, fillColor: feature.properties.tocolor});
              });
              layer.on('mouseout', function(e) {
                 layer.setStyle({weight: 0.2, fillOpacity:.4, fillColor: feature.properties.tocolor});
              });
          }
        });
        
        layersControl.addOverlay(efffArea, 'Effective Fire Fighting Force');

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
          var layers = $scope.shp.getLayers();

          if (layers.length > 1) {
            var features = $scope.shp.toGeoJSON();
            var geom = {
              coordinates: [[]],
              type: "MultiPolygon"
            };

            if ($scope.shp.getLayers().length > 1) {
              geom.coordinates = [[]];
              _.each(features.features, function(e) {
                _.each(e.geometry.coordinates, function(c) {
                  geom.coordinates[0].push(c);
                });
              });
            }
          }
          else {
            var geom = layers[0].toGeoJSON().geometry;
          }

          var fd = new FireDepartment({
            id: config.id,
            geom: geom
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

        //
        // Add layer for Effective Fire Fighting Force
        //
        departmentMap.on('overlayadd', function(layer) {
          layer = layer.layer;
          if ( layer._leaflet_id === efffArea._leaflet_id && efffAreaData){
              showEFFFChart(true);
          }
          else if ( layer._leaflet_id === efffArea._leaflet_id && !efffAreaData) {
            
            departmentMap.spin(true);

            // Get Efff rollup data base on Department 
            EfffChartRollup.query({department: config.id}).$promise.then(function(data) {
                
                if(data.objects.length > 0){
                  // Add Efff Layer and graphic chart
                  $scope.parcel_efff_counts = [
                      {label:"Personnel Coverage", "42+ High Hazards (10.17min)": data.objects[0].parcelcount_high_43_plus, "15+ Unknown Hazards (8min)": data.objects[0].parcelcount_unknown_15_26, "27+ Medium Hazards (8min)": data.objects[0].parcelcount_medium_27_42, "15+ Low Hazards (8min)": data.objects[0].parcelcount_low_15_26}
                  ];

                  if(data.objects[0].drivetimegeom_15_26){

                    //merge geometries
                    var traveltime0 = { "type": "Feature",
                        "properties": {"Name": "Travel Time 8 min", "ToBreak":"15+ Personnel Available", "tocolor": '#74ac49'},
                        "geometry": data.objects[0].drivetimegeom_15_26||null
                    }
                    var traveltime4 = { "type": "Feature",
                        "properties": {"Name": "Travel Time: 8 min", "ToBreak":"27+ Personnel Available", "tocolor":'#f9b380'},//fa8e15
                        "geometry": data.objects[0].drivetimegeom_27_42||null
                    }
                    var traveltime6 = { "type": "Feature",
                        "properties": {"Name": "Travel Time: 10.17 min", "ToBreak":"42+ Personnel Available", "tocolor":'#f89983'},
                        "geometry": data.objects[0].drivetimegeom_43_plus||null
                    }
                    var travelTimeGeom = [traveltime0, traveltime4, traveltime6];
                    efffAreaData = travelTimeGeom;
                    efffArea.addData(travelTimeGeom);
                    layer.setStyle(function(feature) {
                      return {
                        fillColor: feature.properties.tocolor,
                        fillOpacity: .4,
                        weight: 0.2
                      };
                    });
                    departmentMap.fitBounds(efffArea);
                  }
                }
                // Return no data if department hasn't been calculated yet 
                else{
                  $scope.parcel_efff_counts = [
                      {label:"15+ at 8min for Low Hazard", text:"Low", "value": 0},
                      {label:"27+ at 8min for Medium Hazard", text:"Medium", "value": 0},
                      {label:"42+ at 10.17min for High Hazard", text:"High", "value": 0},
                      {label:"15+ at 8min for Unknown Hazard", text:"Unknown", "value": 0}
                  ];
                }
                departmentMap.spin(false);
                showEFFFChart(true);
            });
          }
        });

        //
        //List for Service Area Layer
        //
        departmentMap.on('overlayadd', function(layer) {
          layer = layer.layer;
          if ( layer._leaflet_id === serviceArea._leaflet_id && serviceAreaData){
              showServiceAreaChart(true);
          }
          else if ( layer._leaflet_id === serviceArea._leaflet_id && !serviceAreaData) {
            
            departmentMap.spin(true);

            // Get Service Area rollup data base on Department 
            ServiceAreaRollup.query({department: config.id}).$promise.then(function(data) {
                
                if(data.objects.length > 0){
                  // Add Hazard Layer Info Template
                  $scope.parcel_hazard_level_counts = [
                      {label:"0-4 Minutes", "Low":data.objects[0].parcelcount_low_0_4||0, "Medium":data.objects[0].parcelcount_medium_0_4||0, "High":data.objects[0].parcelcount_high_0_4||0, "Unknown":data.objects[0].parcelcount_unknown_0_4||0},
                      {label:"4-6 Minutes", "Low":data.objects[0].parcelcount_low_4_6||0, "Medium":data.objects[0].parcelcount_medium_4_6||0, "High":data.objects[0].parcelcount_high_4_6||0, "Unknown":data.objects[0].parcelcount_unknown_4_6||0},
                      {label:"6-8 Minutes", "Low":data.objects[0].parcelcount_low_6_8||0, "Medium":data.objects[0].parcelcount_medium_6_8||0, "High":data.objects[0].parcelcount_high_6_8||0, "Unknown":data.objects[0].parcelcount_unknown_6_8||0}
                  ];

                  if(data.objects[0].drivetimegeom_0_4){

                    //merge geometries
                    var traveltime0 = { "type": "Feature",
                        "properties": {"Name": "Travel Time: 0 - 4", "ToBreak":4},
                        "geometry": data.objects[0].drivetimegeom_0_4
                    }
                    var traveltime4 = { "type": "Feature",
                        "properties": {"Name": "Travel Time: 4 - 6", "ToBreak":6},
                        "geometry": data.objects[0].drivetimegeom_4_6
                    }
                    var traveltime6 = { "type": "Feature",
                        "properties": {"Name": "Travel Time: 6 - 8", "ToBreak":8},
                        "geometry": data.objects[0].drivetimegeom_6_8
                    }
                    var travelTimeGeom = [traveltime0, traveltime4, traveltime6];
                    
                    serviceAreaData = travelTimeGeom;
                    serviceArea.addData(travelTimeGeom);
                    layer.setStyle(function(feature) {
                      return {
                        fillColor: '#33cc33',
                        fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5),
                        weight: 0.8
                      };
                    });
                    departmentMap.fitBounds(serviceArea);
                  }
                }
                // Return no data if department hasn't been calculated yet 
                else{
                  $scope.parcel_hazard_level_counts = [
                      {label:"0-4 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
                      {label:"4-6 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
                      {label:"6-8 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
                  ];
                }
                departmentMap.spin(false);
                showServiceAreaChart(true);
            });
          }
        });

        // Get Stations to derive Drive Times and Asset number
        FireStationandStaffing.query({department: config.id}).$promise.then(function(data) {
            $scope.stations = data.objects;

            var numFireStations = $scope.stations.length;
            var serviceAreaURL;

            var deptGeom = {
              x: config.centroid[1],
              y: config.centroid[0]
            };
            if(numFireStations > 1){

                var totalAssetStationString = "";
                var totalAssetStationNumber = 0;
                var assetStationGeom = [];

                //iterate through the station assets
                for (var i = 0; i < numFireStations; i++) {

                    var station = $scope.stations[i];
                    var totalAssets = 0;
                    for (var asset = 0; asset < station.staffingdata.length; asset++) {
                        totalAssets = totalAssets + Number(station.staffingdata[asset].personnel);
                    }

                    if(totalAssets>0){
                        assetStationGeom.push({"geometry":{"x":Number(Number(station.geom.coordinates[0]).toPrecision(4)),"spatialReference":{"wkid":4326},"y":Number(Number(station.geom.coordinates[1]).toPrecision(4))}});
                        totalAssetStationString = totalAssetStationString + String(totalAssets) + ',';
                        totalAssetStationNumber = totalAssetStationNumber + totalAssets;
                    }
                }

                totalAssetStationString = totalAssetStationString.substring(0, totalAssetStationString.length - 1);
                $scope.department_personnel_counts = totalAssetStationNumber + " Personnel/Assets Available";
            }
        });

        function showServiceAreaChart(show) {
            $timeout(function() {
                $scope.showServiceAreaChart = show;
            });
        }

        function showEFFFChart(show) {
            $timeout(function() {
                $scope.showEFFFChart = show;
            });
        }

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
          if (layer.layer._leaflet_id === serviceArea._leaflet_id) {
              showServiceAreaChart(false);
          }
          else if (layer.layer._leaflet_id === efffArea._leaflet_id) {
              showEFFFChart(false);
          }
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
