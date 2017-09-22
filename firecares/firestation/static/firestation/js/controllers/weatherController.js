'use strict';

(function() {
  angular.module('fireStation.weatherWarning', [])
    .controller('weatherWarningController', WeatherWarningController);

  WeatherWarningController.$inject = ['$scope', '$http'];

  function WeatherWarningController($scope, $http) {
    /*$scope.department_states = window.states;
    $scope.input = {
      weather_warnings: null,
      state: null
    };
    $scope.weather_warnings = [];
    $scope.loading = false;
    $scope.$watch('input.state', function(val) {
      if (val) {
        $scope.loading = true;
        $scope.weather_warnings = null;
        $http({
          method: 'GET',
          url: '/api/v1/weather-warning/?limit=2000&fields=warnid,warningname&state=' + val
        }).then(function successCallback(response) {
          $scope.weather_warnings = response.data.objects;
          $scope.loading = false;
        }, function errorCallback(response) {
        });
      }
    });*/
  }
})();