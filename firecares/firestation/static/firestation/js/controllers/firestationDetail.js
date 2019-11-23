'use strict';

(function() {
  angular.module('fireStation.firestationDetailController', ['xeditable', 'ui.bootstrap'])
  .controller('fireStationController', function($scope, $window, $http, Staffing, $timeout, map, FireStation, $filter, $interpolate, $compile, $analytics, WeatherWarning, heatmap, emsHeatmap) {
    var thisFirestation = '/api/v1/firestations/' + config.id + '/';
    var serviceAreaData = null;
    var stationGeom = {
      x: config.geom.coordinates[0],
      y: config.geom.coordinates[1]
    };
    var serviceAreaURL = $interpolate('https://geo.firecares.org/?f=json&Facilities={"features":[{"geometry":{"x":{{x}},"spatialReference":{"wkid":4326},"y":{{y}}}}],"geometryType":"esriGeometryPoint"}&env:outSR=4326&text_input=4,4,4&Break_Values=4 6 8&returnZ=false&returnM=false')(stationGeom);

    $scope.station = FireStation.get({id: config.id});

    var options = {
      boxZoom: true,
      zoom: 15,
      zoomControl: true,
      attributionControl: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      fullscreenControl: false
    };

    $scope.choices = ['Engine', 'Ladder/Truck/Aerial', 'Quint', 'Ambulance/ALS', 'Ambulance/BLS', 'Heavy Rescue',
      'Boat', 'Hazmat', 'Chief', 'Other'];

    $scope.canModifyApparatuses = config.isCurator;
    $scope.forms = [];
    $scope.stations = [];
    $scope.message = {};
    $scope.weather_messages = [];
    $scope.showDetails = false;
    $scope.eventCategory = 'station detail';
    var fitBoundsOptions = {padding: [6, 6]};

    Staffing.query({firestation: config.id}).$promise.then(function(data) {
      $scope.forms = data;
    });

    var map = map.initMap('map', {scrollWheelZoom: false});
    var stationIcon = L.FireCARESMarkers.firestationmarker();
    var headquartersIcon = L.FireCARESMarkers.headquartersmarker();
    var layersControl = L.control.layers().addTo(map);
    var headquartersGeom = config.headquarters ? L.latLng(config.headquarters.coordinates.reverse()) : null;
    var stationGeom = config.geom ? L.latLng(config.geom.coordinates.reverse()) : null;
    var station = L.marker(stationGeom, {icon: stationIcon, zIndexOffset: 1000, draggable: config.draggable});
    var district = null;
    var mouseOverAddedOpacity = 0.25; // put in settings?
    var highlightColor = 'blue';      // put in settings?
    var serviceArea, max;
    var messageboxData = L.control.messagebox({ timeout: 22000, position:'bottomleft' }).addTo(map);

    station.bindPopup('<b>' + config.stationName + '</b>');
    station.addTo(map);
    layersControl.addOverlay(station, 'This Station');

    station.on("dragend", function(e) {
        var html = '<div id="confirmation">Save this as the new location for this station?<br/><br/><span class="editable-buttons"><button type="submit" ng-click="updateGeom([' + e.target.getLatLng().lng +','+ e.target.getLatLng().lat + '])" class="btn btn-primary"><span class="glyphicon glyphicon-ok"></span></button><button type="button" class="btn btn-default" ng-click="closeMapPopup()"><span class="glyphicon glyphicon-remove"></span></button></span></div>';
        var popup = L.popup().setLatLng(e.target.getLatLng())
        .setContent(html);
        setTimeout(function(){popup.openOn(map); $compile($('#confirmation'))($scope);}, 1);

    });

    if ( config.headquarters) {
      var headquarters = L.marker(headquartersGeom, {icon: headquartersIcon, zIndexOffset: 1000});
      headquarters.bindPopup('<b>' + config.headquartersName + '</b>');
      layersControl.addOverlay(headquarters, 'Headquarters Location');
    }

    serviceArea = L.geoJson(null, {
      onEachFeature: function(feature, layer) {
          layer.bindLabel(feature.properties.Name + ' minutes');
          /*var popup = layer.bindPopup(feature.properties.Name + ' minutes');
          popup.on("popupclose", function(e) {
            e.layer.setStyle({weight: 0.8, fillOpacity:-(feature.properties.ToBreak * 0.8 - max) / (max * 1.3), fillColor: '#33cc33'});
          });*/

          layer.on('click', function(e) {
            messageboxData.showforever(feature.properties.Name + ' minutes');
            layer.setStyle({fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5) + mouseOverAddedOpacity, fillColor: highlightColor});
          });
      }
    });

    map.on('click', function(e) {
      serviceArea.setStyle(function(feature) {
        return {
          fillColor: '#33cc33',
          fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5),
          weight: 0.8
        };
      });
      messageboxData.hide();
    });

    layersControl.addOverlay(serviceArea, 'Service Areas');

    if (config.district) {
      district = L.geoJson(config.district, {
        style: function (feature) {
          return {color: '#0074D9', fillOpacity: .05, opacity:.8, weight:2};
        }
      }).addTo(map);
      layersControl.addOverlay(district, 'District');
      map.fitBounds(district.getBounds());
      map.setView(stationGeom);
      heatmap.setClipLayer(district);
      emsHeatmap.setClipLayer(district);
    }
    else {
      map.setView(stationGeom, 15);
    }

    //
    // Weather Warnings
    //
    WeatherWarning.query({department: config.departmentId}).$promise.then(function(data) {

        var weatherPolygons = [];
        var numWarnings = data.objects.length;

        for (var i = 0; i < numWarnings; i++) {
          var warning = data.objects[i];
          var poly = L.multiPolygon(warning.warngeom.coordinates.map(function(d){return mapPolygon(d)}),{color: '#f00', weight:'1px'});
          var warningdate = new Date(warning.expiredate);
          poly.bindPopup('<b>' + warning.prod_type + '</b><br/>Ending: ' + warningdate.toDateString() +' '+ warningdate.toLocaleTimeString() + '<br/><br/><a target="_blank" href='+warning.url+'>Click for More Info</a>');
          weatherPolygons.push(poly);
          $scope.weather_messages.push({class: 'alert-warning', text: '<a class="alert-link" target="_blank" href='+warning.url+'>'+'The Department is under ' + warning.prod_type + '  Until  ' + warningdate.toDateString() +',  '+ warningdate.toLocaleTimeString().replace(':00 ',' ') +'</a>'});
        }

        if (numWarnings > 0) {
          var weatherLayer = L.featureGroup(weatherPolygons);
          weatherLayer.id = 'weather';
          weatherLayer.addTo(map);
          weatherLayer.bringToBack();
          layersControl.addOverlay(weatherLayer, 'Weather Warnings');

          // Hide layer when zoom gets to parcel layer z15
          map.on('zoomend', function() {
            if(map.hasLayer(weatherLayer)){
              if(map.getZoom() > 14){
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
              map.removeLayer(weatherLayer);
          });
        }

        function mapPolygon(poly){
          return poly.map(function(line){return mapLineString(line)})
        }

        function mapLineString(line){
          return line.map(function(d){return [d[1],d[0]]})
        }
    });

    //
    // Heatmap
    //
    var heatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + config.departmentId + '-building-fires.csv';
    $http.head(heatmapDataUrl)
      .then(function(response) {
        var contentLength = Number(response.headers('Content-Length'));

        // Don't show the heatmap layer option for a department with no heatmap data.
        // HACK: A department with no heatmap data will still return the table header for the empty data, which
        //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
        if (contentLength <= 59) {
          return;
        }

        heatmap.init(map);
        $scope.heatmap = heatmap;
        $scope.showHeatmapCharts = false;

        layersControl.addOverlay(heatmap.layer, 'Fires Heatmap');
        map.on('overlayadd', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeIn('slow');
            $scope.showDetails = false;
          }
          else if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
            if (heatmap.isDownloaded) {
              showHeatmapCharts(true);
            } else {
              map.spin(true);
              heatmap.download(heatmapDataUrl)
                .then(function() {
                  showHeatmapCharts(true);
                }, function(err) {
                  alert(err.message);
                  layersControl.removeLayer(heatmap.layer);
                })
                .finally(function() {
                  map.spin(false);
                })
              ;
            }
          }
        });

        map.on('overlayremove', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeOut('slow');
          }
          else if (layer.layer._leaflet_id === heatmap.layer._leaflet_id) {
            showHeatmapCharts(false);
          }
          // if(layer.layer._leaflet_id === activeFires._leaflet_id){
          //   map.removeControl(activeFirelegend);
          // }
        });

        function showHeatmapCharts(show) {
          $timeout(function() {
            $scope.showHeatmapCharts = show;
            if(show === true) {
              // Removes the ems heatmap and unchecks the control.
              $scope.showEMSHeatmapCharts = false;
              if(map.hasLayer(emsHeatmap.layer)) {
                map.removeLayer(emsHeatmap.layer);
              }
            }
          });
        }
      });

    //
    // EMS Heatmap
    //
    var emsHeatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + config.departmentId + '-ems-incidents.csv';
    $http.head(emsHeatmapDataUrl)
      .then(function(response) {
        var contentLength = Number(response.headers('Content-Length'));

        // Don't show the ems heatmap layer option for a department with no ems heatmap data.
        // HACK: A department with no ems heatmap data will still return the table header for the empty data, which
        //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
        if (contentLength <= 59) {
          return;
        }

        emsHeatmap.init(map, {
          gradient: { 0.55: '#7400ff', 0.65: '#3333ff', 1: '#ff3333' },
        });
        $scope.emsHeatmap = emsHeatmap;
        $scope.showEMSHeatmapCharts = false;

        layersControl.addOverlay(emsHeatmap.layer, 'EMS Heatmap');
        map.on('overlayadd', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeIn('slow');
            $scope.showDetails = false;
          }
          else if (layer.layer._leaflet_id === emsHeatmap.layer._leaflet_id) {
            if (emsHeatmap.isDownloaded) {
              showEMSHeatmapCharts(true);
            } else {
              map.spin(true);
              emsHeatmap.download(emsHeatmapDataUrl)
                .then(function() {
                  showEMSHeatmapCharts(true);
                }, function(err) {
                  alert(err.message);
                  layersControl.removeLayer(emsHeatmap.layer);
                })
                .finally(function() {
                  map.spin(false);
                })
              ;
            }
          }
        });

        map.on('overlayremove', function(layer) {
          if(layer.layer.id === 'weather'){
            $('.weather-messages').fadeOut('slow');
          }
          else if (layer.layer._leaflet_id === emsHeatmap.layer._leaflet_id) {
            showEMSHeatmapCharts(false);
          }
          // if(layer.layer._leaflet_id === activeFires._leaflet_id){
          //   map.removeControl(activeFirelegend);
          // }
        });

        function showEMSHeatmapCharts(show) {
          $timeout(function() {
            $scope.showEMSHeatmapCharts = show;

            if(show === true) {
              // Remove Fires heatmap if its on
              $scope.showHeatmapCharts = false; // Hides filters
              // Removes the heatmap and unchecks the control.
              if(map.hasLayer(heatmap.layer)) {
                map.removeLayer(heatmap.layer);
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
              .openOn(map);
          }
        }
      }
    });
    layersControl.addOverlay(parcels, 'Parcels');

    map.on('overlayadd', function(layer) {
      layer = layer.layer;
      if(layer.id === 'weather'){
        $('.weather-messages').fadeIn('slow');
        $scope.showDetails = false;
      }
      else if ( layer._leaflet_id === serviceArea._leaflet_id && !serviceAreaData) {
        map.spin(true);
        $http({
          method: 'GET',
          url: serviceAreaURL
        }).then(function success(resp) {
          esri2geo.toGeoJSON(resp.data.results[0].value, function(_, geojson) {
            var values = geojson.features.map(function(val, idx) {
              return val.properties.ToBreak;
            });
            max = Math.max.apply(null, values);
            serviceAreaData = geojson;
            serviceArea.addData(geojson);
            layer.setStyle(function(feature) {
              return {
                fillColor: '#33cc33',
                fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5),
                weight: 0.8
              };
            });
            map.fitBounds(serviceArea);
            map.spin(false);
          });
        }, function error(err) {
          map.spin(false);
        });
      }
    });

    map.on('overlayadd', function(layer) {
      $analytics.eventTrack('enable layer', {
        category: $scope.eventCategory + ': map',
         label: layer.name
       });
    });

    map.on('fullscreenchange', function(e) {
      status = e.target.isFullscreen() ? 'enable' : 'disable';
      $analytics.eventTrack(status + ' full screen', {
        category: $scope.eventCategory + ': map'
      });
    });

    map.on('overlayremove', function(layer) {
      if(layer.layer.id === 'weather'){
          $('.weather-messages').fadeOut('slow');
      }
      $analytics.eventTrack('disable layer', {
        category: $scope.eventCategory + ': map',
        label: layer.name
      });

      messageboxData.hide();
    });

    $scope.closeMapPopup = function() {
        return map.closePopup();
    };

    $scope.updateGeom = function(coords) {
        $scope.station.geom.coordinates = coords;
        $scope.updateStation().$promise.then(function(data){
            $scope.closeMapPopup();
        });
    };

    $scope.ClearForm = function(form) {
      form.apparatus = 'Engine';
      form.personnel = 0;
    };

    $scope.AddForm = function() {
      var newForm = new Staffing({'apparatus': 'Engine',
        'personnel': 0,
        'firestation': thisFirestation,
        'id': new Date().getUTCMilliseconds(),
        'new_form': true
      });

      $scope.forms.push(newForm);
      $timeout($scope.showLastTab);
    };

    $scope.UpdateForm = function(form) {
      if (form['apparatus'] != 'Other') {
        form['other_apparatus_type'] = '';
      }

      if (form.new_form === true) {

        //remove temp variables
        delete form['new_form'];
        delete form['id'];

        form.$save(form, function(formResponse) {
          form.id = formResponse.id;
          $timeout($scope.showLastTab);
          $scope.showMessage(form.apparatus + ' staffing has been updated.');
        });

        return;
      }

      form.$update({id:form.id}, function() {
        $scope.showMessage(form.apparatus + ' staffing has been updated.');
      }, function() {
        $scope.showMessage('There was a problem updating the ' + form.apparatus + ' staffing.', 'danger');
      });
    };

    $scope.showLastTab = function() {
      $('.apparatus-tabs li a:last').tab('show');
    };

    $scope.DeleteForm = function(form) {

      if (form.new_form === true) {
        $scope.forms.splice($scope.forms.indexOf(form), 1);
        $scope.showMessage(form.apparatus + ' staffing has been deleted.');
        return;
      }

      form.$delete({id:form.id}, function(){
        $scope.forms.splice($scope.forms.indexOf(form), 1);
        $scope.showMessage(form.apparatus + ' staffing has been deleted.');
        $scope.showLastTab();
      }, function(){
        $scope.showMessage('There was an error deleting the staffing for ' + form.apparatus + '.', 'danger');
      });
    };

    $scope.toggleFullScreenMap = function() {
        map.toggleFullscreen();
    };

    $scope.updateStation = function() {
        return FireStation.update({id: $scope.station.id}, $scope.station);
      };

    $scope.showMessage = function(message, message_type) {
      /*
       message_type should be one of the bootstrap alert classes (error, success, info, warning, etc.)
       */
      var message_class = message_type || 'success';

      $scope.message = {message: message, message_class: message_class};
      $('#response-capability-message').show();

      setTimeout(function() {
        $('#response-capability-message').fadeOut('slow');
        $scope.message = {};
      }, 4000);
    };

    // Update district boundaries
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
            $scope.shp.addTo(map);
            map.fitBounds($scope.shp);
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

      $scope.station.district = geom;

      FireStation.update({id: $scope.station.id}, $scope.station).$promise.then(function() {
        // Remove old district boundary
        if (district) {
          map.removeLayer(district);
          layersControl.removeLayer(district);
        }
        district = $scope.shp;
        district.setStyle({color: '#0074D9', fillOpacity: .05, opacity: .8, weight: 2});
        layersControl.addOverlay(district, 'District');
        $scope.shp = null;
        $scope.messages = [];
        $scope.messages.push({class: 'alert-success', text: 'Fire station district boundary updated.'});
      }, function() {
        $scope.messages.push({class: 'alert-danger', text: 'Server issue updating district boundary.'});
      });
    };

    $scope.cancelBoundary = function() {
      map.removeLayer($scope.shp);
      $scope.shp = null;
      angular.element("form[name='boundaryUpload']").get(0).reset();
    };
  })
})();
