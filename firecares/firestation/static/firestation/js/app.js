'use strict';

(function() {
  angular.module('fireStation', [
      'ngResource',
      'fireStation.factories',
      'fireStation.homeController',
      'fireStation.departmentDetailController',
      'fireStation.performanceScoreController',
      'fireStation.mapService',
      'fireStation.gauge',
      'fireStation.search',
      'fireStation.graphs'
  ])

  .config(function($interpolateProvider, $httpProvider, $resourceProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })

})();

