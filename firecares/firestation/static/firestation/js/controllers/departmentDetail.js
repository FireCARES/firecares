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

  JurisdictionController.$inject = ['$scope', '$timeout', '$http', 'FireStation', 'map', 'heatmap', 'emsHeatmap', '$filter', 'FireDepartment', '$analytics', 'WeatherWarning', '$interpolate', 'FireStationandStaffing', 'ServiceAreaRollup', 'EfffChartRollup'];

  function JurisdictionController($scope, $timeout, $http, FireStation, map, heatmap, emsHeatmap, $filter, FireDepartment, $analytics, WeatherWarning, $interpolate, FireStationandStaffing, ServiceAreaRollup, EfffChartRollup) {
    var departmentMap = map.initMap('map', {scrollWheelZoom: false});
    var messagebox = L.control.messagebox({ timeout: 11000, position:'bottomright' }).addTo(departmentMap);
    var messageboxData = L.control.messagebox({ timeout: 22000, position:'bottomleft' }).addTo(departmentMap);
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
    $scope.showDetails = false;
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
    var activeFires,activeFiresData;
    var activefireURL = 'https://wildfire.cr.usgs.gov/arcgis/rest/services/geomac_fires/FeatureServer/3/query?outFields=*&f=json&outSR=4326&inSR=4326&geometryType=esriGeometryEnvelope&geometry=';

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
      var relevantwarnings = false;
      var relevantwarninglist = ['High Wind Watch', "High Wind Warning", "Air Stagnation Advisory", "Lake Wind Advisory", "Fire Weather Warning", "Wind Advisory", "Gale Watch", "Fire Weather Watch", "Red Flag Warning", "Gale Warning"];
      var warningurllist = []; //not showing duplicate urls

      for (var i = 0; i < numWarnings; i++) {
        var warning = data.objects[i];

        if(relevantwarninglist.indexOf(warning.prod_type) > -1){
          relevantwarnings = true;
        }

        if(warningurllist.indexOf(warning.url) == -1){

          var poly = L.multiPolygon(warning.warngeom.coordinates.map(function(d){return mapPolygon(d)}),{color: '#f00', weight:'1px'});
          var warningdate = new Date(warning.expiredate);
          poly.bindPopup('<b>' + warning.prod_type + '</b><br/>Ending: ' + warningdate.toDateString() +' '+ warningdate.toLocaleTimeString() + '<br/><br/><a target="_blank" href='+warning.url+'>Click for More Info</a>');
          weatherPolygons.push(poly);
          $scope.weather_messages.push({class: 'alert-warning', text: '<a class="alert-link" target="_blank" href='+warning.url+'>'+' ' + warning.prod_type + '  Until  ' + warningdate.toDateString() +',  '+ warningdate.toLocaleTimeString().replace(':00 ',' ') +'</a>'});
          warningurllist.push(warning.url);
        }
      }

      if (numWarnings > 0) {
        var weatherLayer = L.featureGroup(weatherPolygons);
        weatherLayer.id = 'weather';

        if(relevantwarnings){
          weatherLayer.addTo(departmentMap); //deafult on only if there is wind or fire warning
          weatherLayer.bringToBack();
        }

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

        // Remove layer when Weather messages are hidden
        $('.weather-messages').on('weatherWarningsHidden', function () {
          departmentMap.removeLayer(weatherLayer);
        });
      }

      function mapPolygon(poly){
        return poly.map(function(line){return mapLineString(line)})
      }


      function mapLineString(line){
        return line.map(function(d){return [d[1],d[0]]})
      }
    });

    if (config.geom != null) {
      countyBoundary = L.geoJson(config.geom, {
        style: function(feature) { return {
          color: '#0074D9',
          fillOpacity: .05,
          opacity: .8,
          weight: 2,
          pointerEvents: 'none',
          cursor: 'default',
          clickable: false,
          interactive: false};
        },
        clickable: false,
        interactive: false,
      }).addTo(departmentMap);
      layersControl.addOverlay(countyBoundary, 'Jurisdiction Boundary');
      departmentMap.fitBounds(countyBoundary.getBounds(), fitBoundsOptions);
    } else {
      departmentMap.setView(config.centroid, 13);
    }

    if (config.centroid != null) {
      var headquarters = L.marker(config.centroid, {icon: headquartersIcon, zIndexOffset: 1000});
      headquarters.addTo(departmentMap);
      layersControl.addOverlay(headquarters, 'Headquarters Location');
    }

    $scope.toggleFullScreenMap = function() {
      departmentMap.toggleFullscreen();
    };

    //
    // Active Fires
    //
    var activeFirelegend = L.control({position: 'bottomleft'});

    activeFirelegend.onAdd = function (map) {

      var div = L.DomUtil.create('div', 'info legend');
      div.innerHTML = '<i style="background:#f4f4f4;border-color:#e2301f;border-width:2.5px;border-style:dashed;"></i> Active Burning Fires<br>';
      div.innerHTML += '<i style="background:#f4f4f4;border-color:#f28715;border-width:2.5px;border-style:dashed;"></i> Last 12-24 hrs<br>';
      div.innerHTML += '<i style="background:#f4f4f4;border-color:#353433;border-width:2.5px;border-style:dashed;"></i> Last 24-48 hrs<br>';
      return div;
    };

    activeFires = L.geoJson(null, {
      onEachFeature: function(feature, layer) {
        layer.bindPopup("Reported: " + feature.properties.date_ + "<br>Active Fire: " + feature.properties.load_stat);
        layer.on('mouseover', function(e) {
          layer.setStyle({fillOpacity: 1});
        });
        layer.on('mouseout', function(e) {
          layer.setStyle({fillOpacity:.2});
        });
      }
    });

    layersControl.addOverlay(activeFires, 'Active Wildland Fires');

    departmentMap.on('overlayadd', function(layer) {
      layer = layer.layer;
      if ( layer._leaflet_id === activeFires._leaflet_id && !activeFiresData) {
        departmentMap.spin(true);
        if (config.geom != null){
          var deptbbox = countyBoundary.getBounds().pad(1).toBBoxString();//1 % bigger bbox
        }
        else{
          var corner1 = L.latLng(config.centroid[0]-.5, config.centroid[1]-.5),
            corner2 = L.latLng(config.centroid[0]+.5, config.centroid[1]+.5),
            bounds = L.latLngBounds(corner1, corner2);

          departmentMap.fitBounds(bounds);
          var deptbbox = bounds.pad(1).toBBoxString();//1 % bigger bbox
        }
        $http({
          method: 'GET',
          url: activefireURL+deptbbox
        }).then(function success(resp) {
          esri2geo.toGeoJSON(resp.data, function(_, geojson) {

            if(geojson.features.length > 0){
              activeFiresData = geojson;
              activeFires.addData(geojson);
              layer.setStyle(function(feature) {
                var activeFiresstyle = {};
                if(feature.properties.load_stat == "Active Burning"){
                  activeFiresstyle = {
                    fillColor: '#f4f4f4',
                    fillOpacity: .1,
                    weight: 3,
                    opacity: 1,
                    dashArray: '5,10',
                    color: '#e2301f'
                  };
                }
                else if(feature.properties.load_stat == "Last 24-48 hrs"){
                  activeFiresstyle = {
                    fillColor: '#f4f4f4',
                    fillOpacity: .1,
                    weight: 3,
                    opacity: 1,
                    dashArray: '5,10',
                    color: '#f28715'
                  };
                }
                else {
                  activeFiresstyle = {
                    fillColor: '#f4f4f4',
                    fillOpacity: .1,
                    weight: 3,
                    opacity: 1,
                    dashArray: '5,10',
                    color: '#353433'
                  };
                }
                return activeFiresstyle;
              });
              departmentMap.fitBounds(activeFires);
              departmentMap.spin(false);
              messagebox.show(geojson.features.length + ' total Active Wildland Fires in the vicinity of this department');

              if(layer._leaflet_id === activeFires._leaflet_id){
                departmentMap.addControl(activeFirelegend);
              }
            }
            else{
              messagebox.show('There are no Active Wildland Fires in the vicinity of this department');
              departmentMap.spin(false);
            }
          });
        }, function error(err) {
          departmentMap.spin(false);
        });
      }
    });

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
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeIn('slow');
            $scope.showDetails = false;
          }
          else if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
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
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeOut('slow');
          }
          else if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
            showHeatmapCharts(false);
          }
          if(layer.layer._leaflet_id === activeFires._leaflet_id){
            departmentMap.removeControl(activeFirelegend);
          }
        });

        function showHeatmapCharts(show) {
          $timeout(function() {
            $scope.showHeatmapCharts = show;
            if(show === true) {
              // Removes the ems heatmap and unchecks the control.
              $scope.showEMSHeatmapCharts = false;
              if(departmentMap.hasLayer(emsHeatmap.layer)) {
                departmentMap.removeLayer(emsHeatmap.layer);
                layersControl.update();
              }
            }
          });
        }
      });

    //
    // EMS Heatmap
    //
    var emsHeatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + config.id + '-ems-incidents.csv';
    $http.head(emsHeatmapDataUrl)
      .then(function(response) {
        var contentLength = Number(response.headers('Content-Length'));

        // Don't show the ems heatmap layer option for a department with no ems heatmap data.
        // HACK: A department with no ems heatmap data will still return the table header for the empty data, which
        //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
        if (contentLength <= 59) {
          return;
        }

        emsHeatmap.init(departmentMap);
        $scope.emsHeatmap = emsHeatmap;
        $scope.showEMSHeatmapCharts = false;

        layersControl.addOverlay(emsHeatmap.layer, 'EMS Heatmap');
        departmentMap.on('overlayadd', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeIn('slow');
            $scope.showDetails = false;
          }
          else if (layer.layer._leaflet_id === emsHeatmap.layer._leaflet_id) {
            if (emsHeatmap.heat) {
              showEMSHeatmapCharts(true);
            } else {
              departmentMap.spin(true);
              emsHeatmap.download(emsHeatmapDataUrl)
                .then(function() {
                  showEMSHeatmapCharts(true);
                }, function(err) {
                  alert(err.message);
                  layersControl.removeLayer(emsHeatmap.layer);
                })
                .finally(function() {
                  departmentMap.spin(false);
                })
              ;
            }
          }
        });

        departmentMap.on('overlayremove', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeOut('slow');
          }
          else if (layer.layer._leaflet_id === emsHeatmap.layer._leaflet_id) {
            showEMSHeatmapCharts(false);
          }
          if(layer.layer._leaflet_id === activeFires._leaflet_id){
            departmentMap.removeControl(activeFirelegend);
          }
        });

        function showEMSHeatmapCharts(show) {
          $timeout(function() {
            $scope.showEMSHeatmapCharts = show;

            if(show === true) {
              // Remove Fires heatmap if its on
              $scope.showHeatmapCharts = false; // Hides filters
              // Removes the heatmap and unchecks the control.
              if(departmentMap.hasLayer(heatmap.layer)) {
                departmentMap.removeLayer(heatmap.layer);
                layersControl.update();
              }
            }
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

    $scope.updateFireDepartment = function() {
      var fd = new FireDepartment({
        id: config.id,
        boundary_verified:true,
        staffing_verified:true,
        stations_verified:true
      });
      fd.$update().then(function() {
        $scope.messages = [];
        $scope.messages.push({class: 'alert-success', text: 'Department updated.'});
      }, function() {
        $scope.messages.push({class: 'alert-danger', text: 'Server issue updating Department Information.'});
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

    //need  login to view Service area
    if (config.showParcels) {
      //
      // Service Area
      //
      serviceArea = L.geoJson(null, {
        onEachFeature: function(feature, layer) {
          layer.bindLabel(feature.properties.Name + ' minutes');

          layer.on('click', function(e) {
            messageboxData.showforever(feature.properties.Name + ' minutes');
            e.layer.setStyle({fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5) + mouseOverAddedOpacity, fillColor: highlightColor});
          });
        }
      });

      layersControl.addOverlay(serviceArea, 'Service Areas');

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
                    fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.2),
                    weight: 0.8,color:'#003300'
                  };
                });
                departmentMap.fitBounds(serviceArea);
                messagebox.show('Service Area Information added to the map.');
              }
            }
            // Return no data if department hasn't been calculated yet
            else{
              $scope.parcel_hazard_level_counts = [
                {label:"0-4 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
                {label:"4-6 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
                {label:"6-8 Minutes", "High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
              ];

              messagebox.show('Service Area Analysis requires valid Personnel entries.');
            }
            departmentMap.spin(false);
            showServiceAreaChart(true);
          });
        }
      });

      //
      // Add layer for Effective Fire Fighting Force removed config.superUser requirement
      //
      efffArea = L.geoJson(null, {
        onEachFeature: function(feature, layer) {
          layer.bindLabel(feature.properties.Name + '<br>'+ feature.properties.ToBreak);

          layer.on('click', function(e) {
            messageboxData.showforever(feature.properties.Name + '<br>'+ feature.properties.ToBreak);
            e.layer.setStyle({weight: .7,fillOpacity: .9, fillColor: feature.properties.tocolor, color:'#fff', opacity:.8});
          });
        }
      });

      layersControl.addOverlay(efffArea, 'Effective Response Force');

      departmentMap.on('overlayadd', function(layer) {
        layer = layer.layer;
        if ( layer._leaflet_id === efffArea._leaflet_id && efffAreaData){
          showEFFFChart(true);
        }
        else if ( layer._leaflet_id === parcels._leaflet_id){
          messagebox.show('Zoom into the map area to view parcels');
        }
        else if ( layer._leaflet_id === efffArea._leaflet_id && !efffAreaData) {

          departmentMap.spin(true);

          // Get Efff rollup data base on Department
          EfffChartRollup.query({department: config.id}).$promise.then(function(data) {

            if(data.objects.length > 0){
              $scope.parcel_efff_counts = [
                {label:"# Parcels Covered", "42+ High Hazards (10.17min)": data.objects[0].parcelcount_high_43_plus, "15+ Unknown Hazards (8min)": data.objects[0].parcelcount_unknown_15_26, "27+ Medium Hazards (8min)": data.objects[0].parcelcount_medium_27_42, "15+ Low Hazards (8min)": data.objects[0].parcelcount_low_15_26, '38': false},
                {label:"% Parcel Coverage", "42+ High Hazards (10.17min)": data.objects[0].perc_covered_high_43_plus, "15+ Unknown Hazards (8min)": data.objects[0].perc_covered_unknown_15_26, "27+ Medium Hazards (8min)": data.objects[0].perc_covered_medium_27_42, "15+ Low Hazards (8min)": data.objects[0].perc_covered_low_15_26, '38': false}
              ];

              // Add Efff Layer and graphic chart if there is geometry
              if(data.objects[0].drivetimegeom_15_26){

                //merge geometries
                var traveltime0 = { "type": "Feature",
                  "properties": {"Name": "Travel Time: 8 min", "ToBreak":"15+ Personnel Available", "tocolor": '#74ac49', "hazard":'Low'},
                  "geometry": data.objects[0].drivetimegeom_15_26||null
                }
                var traveltime4 = { "type": "Feature",
                  "properties": {"Name": "Travel Time: 8 min", "ToBreak":"27+ Personnel Available", "tocolor":'#f9b380', "hazard":'Medium'},
                  "geometry": data.objects[0].drivetimegeom_27_42||null
                }

                if(config.emsTransport){
                  var traveltime6 = { "type": "Feature",
                    "properties": {"Name": "Travel Time: 10.17 min", "ToBreak":"38+ Personnel Available", "tocolor":'#f89983', "hazard":'High'},
                    "geometry": data.objects[0].drivetimegeom_38_plus||null
                  }
                  $scope.parcel_efff_counts = [
                    {label:"# Parcels Covered", "38+ High Hazards (10.17min)": data.objects[0].parcelcount_high38_plus, "15+ Unknown Hazards (8min)": data.objects[0].parcelcount_unknown_15_26, "27+ Medium Hazards (8min)": data.objects[0].parcelcount_medium_27_42, "15+ Low Hazards (8min)": data.objects[0].parcelcount_low_15_26, '38': true},
                    {label:"% Parcel Coverage", "38+ High Hazards (10.17min)": data.objects[0].perc_covered_high38_plus, "15+ Unknown Hazards (8min)": data.objects[0].perc_covered_unknown_15_26, "27+ Medium Hazards (8min)": data.objects[0].perc_covered_medium_27_42, "15+ Low Hazards (8min)": data.objects[0].perc_covered_low_15_26, '38': true}
                  ];
                }
                else{
                  var traveltime6 = { "type": "Feature",
                    "properties": {"Name": "Travel Time: 10.17 min", "ToBreak":"42+ Personnel Available", "tocolor":'#f89983', "hazard":'High'},
                    "geometry": data.objects[0].drivetimegeom_43_plus||null
                  }
                }

                var travelTimeGeom = [traveltime0, traveltime4, traveltime6];
                efffAreaData = travelTimeGeom;
                efffArea.addData(travelTimeGeom);
                layer.setStyle(function(feature) {
                  return {
                    fillColor: feature.properties.tocolor,
                    fillOpacity: .4, weight:1, color:'#fff', opacity:.8
                  };
                });
                departmentMap.fitBounds(efffArea);
                messagebox.show('Effective Fire Fighting Force added to the map.');
              }
            }
            // Return no data if department hasn't been calculated yet
            else{
              $scope.parcel_efff_counts = [
                {label:"Personnel Coverage", "42+ High Hazards (10.17min)": 0, "15+ Unknown Hazards (8min)": 0, "27+ Medium Hazards (8min)": 0, "15+ Low Hazards (8min)": 0}
              ];

              messagebox.show('Effective Fire Fighting Force requires valid Personnel entries.');
            }
            departmentMap.spin(false);
            showEFFFChart(true);

            document.addEventListener("efffHighlight", function (e) {
              for (var l in efffArea._layers) {
                if(efffArea._layers[l].feature.properties.hazard == e.detail){
                  efffArea._layers[l].setStyle({weight: .7,fillOpacity: .9, fillColor: efffArea._layers[l].feature.properties.tocolor, color:'#fff', opacity:.8});
                }
                else{
                  efffArea._layers[l].setStyle({weight: 0.1, fillOpacity:0, fillColor: efffArea._layers[l].feature.properties.tocolor, color:'#fff', opacity:.8});
                }
              };
            });
            document.addEventListener("uNefffHighlight", function (e) {
              for (var l in efffArea._layers) {
                efffArea._layers[l].setStyle({weight: 0.1, fillOpacity:0.4, fillColor: efffArea._layers[l].feature.properties.tocolor, color:'#fff', opacity:.8});
              };
            });
          });
        }
      });
    }

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
        if(totalAssetStationNumber == 0){
          $scope.department_personnel_counts = "Analysis tools require valid Personnel Entries"
        }
        else{
          $scope.department_personnel_counts = totalAssetStationNumber + " Personnel/Assets Available";
        }
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

    departmentMap.on('click', function(e) {
      serviceArea.setStyle(function(feature) {
        return {
          fillColor: '#33cc33',
          fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5),
          weight: 0.8
        };
      });
      efffArea.setStyle(function(feature) {
        return {
          fillColor: feature.properties.tocolor,
          fillOpacity: .4, weight:1, color:'#fff', opacity:.8
        };
      });
      messageboxData.hide();
    });

    departmentMap.on('overlayremove', function(layer) {
      $analytics.eventTrack('disable layer', {
        category: eventCategory + ': map',
        label: layer.name
      });

      messageboxData.hide();

      if(serviceArea) {
        if (layer.layer._leaflet_id === serviceArea._leaflet_id) {
          showServiceAreaChart(false);
        }
      }
      if(efffArea){
        if (layer.layer._leaflet_id === efffArea._leaflet_id) {
          showEFFFChart(false);
        }
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
      _.throttle(heatMapFiltered, 500, {trailing: true}));

    $timeout(function() {
      angular.element(".loading").fadeOut();
    }, 0);
  }
})();
