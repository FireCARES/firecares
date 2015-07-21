'use strict';

(function() {
  angular.module('fireStation', ['ngResource',
      'fireStation.factories',
      'fireStation.departmentDetailController',
      'fireStation.mapService'
  ])

  .config(function($interpolateProvider, $httpProvider, $resourceProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })

})();

