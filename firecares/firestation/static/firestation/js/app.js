'use strict';

(function() {
  angular.module('fireStation', ['ngResource',
      'fireStation.factories',
      'fireStation.departmentDetailController',
      'fireStation.mapService',
      'fireStation.gauge',
      'fireStation.search'
  ])

  .config(function($interpolateProvider, $httpProvider, $resourceProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })

})();

