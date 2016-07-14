'use strict';

(function() {
  angular.module('fireStation', [
      'ngResource',
      'fireStation.factories',
      'fireStation.homeController',
      'fireStation.departmentDetailController',
      'fireStation.firestationDetailController',
      'fireStation.performanceScoreController',
      'fireStation.mapService',
      'fireStation.heatmapService',
      'fireStation.favoriteService',
      'fireStation.gauge',
      'fireStation.search',
      'fireStation.graphs',
      'fireStation.map',
      'ui.bootstrap',
      'mapstory.uploader'
  ])

  .config(function($interpolateProvider, $httpProvider, $resourceProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })

})();
