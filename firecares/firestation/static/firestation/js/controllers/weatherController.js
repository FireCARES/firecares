'use strict';

(function() {
  angular.module('fireStation.weatherWarning', [])
    .controller('weatherWarningController', WeatherWarningController);

  WeatherWarningController.$inject = ['$scope', '$http'];

  function WeatherWarningController($scope, $http) {

  }
})();