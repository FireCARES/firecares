'use strict';

(function() {
  angular.module('fireStation.firestationDetailController', ['xeditable', 'ui.bootstrap'])
  .controller('fireStationController', function($scope, $window, $http, Staffing, $timeout, map, FireStation, $filter, $interpolate, $compile, $analytics, WeatherWarning) {
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
          layer.bindPopup(feature.properties.Name + ' minutes');
          layer.on('mouseover', function(e) {
             layer.setStyle({fillOpacity: -(feature.properties.ToBreak * 0.8 - max) / (max * 1.5) + mouseOverAddedOpacity, fillColor: highlightColor, weight: 4});
          });
          layer.on('mouseout', function(e) {
             layer.setStyle({weight: 0.8, fillOpacity:-(feature.properties.ToBreak * 0.8 - max) / (max * 1.5), fillColor: '#33cc33', weight: 1});
          });
      }
    });

    layersControl.addOverlay(serviceArea, 'Service area');

    if (config.district) {
      district = L.geoJson(config.district, {
        style: function (feature) {
          return {color: '#0074D9', fillOpacity: .05, opacity:.8, weight:2};
        }
      }).addTo(map);
      layersControl.addOverlay(district, 'District');
      map.fitBounds(district.getBounds());
      map.setView(stationGeom);
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
        }

        function mapPolygon(poly){
          return poly.map(function(line){return mapLineString(line)})
        }

        function mapLineString(line){
          return line.map(function(d){return [d[1],d[0]]})  
        }
    });

    map.on('overlayadd', function(layer) {
      layer = layer.layer;
      if ( layer._leaflet_id === serviceArea._leaflet_id && !serviceAreaData) {
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
      $analytics.eventTrack('disable layer', {
        category: $scope.eventCategory + ': map',
        label: layer.name
      });
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
