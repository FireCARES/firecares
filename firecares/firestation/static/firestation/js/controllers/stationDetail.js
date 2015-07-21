'use strict';

(function() {
    angular.module('fireStation.stationDetailController', [])

    .controller('fireStationController', function($scope, $window, $http, Staffing, $timeout, map) {

          var thisFirestation = '/api/v1/firestations/' + config.id + '/';

          $scope.choices = ['Engine', 'Ladder/Truck/Aerial', 'Quint', 'Ambulance/ALS', 'Ambulance/BLS', 'Heavy Rescue',
              'Boat', 'Hazmat', 'Chief', 'Other'];

          $scope.forms = [];
          $scope.message = {};
          var fitBoundsOptions = {padding: [6, 6]};

          Staffing.query({firestation: config.id}).$promise.then(function(data){
              if ( !data.length ) {
                $scope.AddForm();
                return;
              }

              $scope.forms = data;
          });

          var stationMap = map.initMap('map');
          stationMap.setView(config.centroid, 15);
          L.marker(config.centroid, {icon: L.FireCARESMarkers.firestationmarker()}).addTo(stationMap);

          if (config.geom != null) {
            var districtBoundary = L.geoJson(config.geom, {
              style: function (feature) {
                  return {color: '#0074D9', fillOpacity: .05, opacity: .8, weight:2 };
              }
            }).addTo(stationMap);
            stationMap.fitBounds(districtBoundary.getBounds(), fitBoundsOptions);
          }

          L.tileLayer('https://{s}.tiles.mapbox.com/v3/examples.map-i87786ca/{z}/{x}/{y}.png',
              {'attribution': '© Mapbox'}).addTo(stationMap);


          $scope.ClearForm = function(form) {
              form.apparatus = 'Engine';
              form.firefighter = 0;
              form.firefighter_emt = 0;
              form.firefighter_paramedic = 0;
              form.ems_emt = 0;
              form.ems_paramedic = 0;
              form.officer = 0;
              form.officer_paramedic = 0;
              form.ems_supervisor = 0;
              form.chief = 0;
          };

          $scope.AddForm = function() {
              var newForm = new Staffing({'apparatus': 'Engine',
                  'chief_officer': 0,
                  'ems_emt': 0,
                  'ems_paramedic': 0,
                  'ems_supervisor': 0,
                  'firefighter': 0,
                  'firefighter_emt': 0,
                  'firefighter_paramedic': 0,
                  'firestation': thisFirestation,
                  'officer': 0,
                  'officer_paramedic': 0,
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
                $scope.showMessage('There was a problem updating the ' + form.apparatus + ' staffing.', 'error');
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
                  $scope.showMessage('There was an error deleting the staffing for ' + form.apparatus + '.', 'error');
              });
          };

          $scope.ClearForm = function(form) {
              form.apparatus = 'Engine';
              form.firefighter = 0;
              form.firefighter_emt = 0;
              form.firefighter_paramedic = 0;
              form.ems_emt = 0;
              form.ems_paramedic = 0;
              form.officer = 0;
              form.officer_paramedic = 0;
              form.ems_supervisor = 0;
              form.chief = 0;
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
      });

})();