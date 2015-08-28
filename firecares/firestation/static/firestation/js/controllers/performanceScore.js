'use strict';

(function() {
    angular.module('fireStation.performanceScoreController', [])

    .controller('performanceScore', function($scope) {
      $scope.randInt = function(min, max) {
          return Math.floor((Math.random() * max) + min);
      }
      $scope.value = $scope.randInt(0, 200);
      })
})();

