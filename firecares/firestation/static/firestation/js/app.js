'use strict';

(function() {
  angular.module('fireStation', [
      'ngResource',
      'fireStation.factories',
      'fireStation.homeController',
      'fireStation.departmentDetailController',
      'fireStation.departmentDetailController.userAdmin',
      'fireStation.departmentDetailController.whitelistAdmin',
      'fireStation.departmentDetailController.userInvite',
      'fireStation.departmentSelection',
      'fireStation.requestApproval',
      'fireStation.firestationDetailController',
      'fireStation.performanceScoreController',
      'fireStation.mapService',
      'fireStation.heatmapService',
      'fireStation.favoriteService',
      'fireStation.gauge',
      'fireStation.search',
      'fireStation.graphs',
      'fireStation.map',
      'fireStation.feedback',
      'ui.bootstrap',
      'mapstory.uploader'
  ])

  .filter('defaultValue', function() {
    return function(input, default_value) {
      return (input !== null && input !== '') ? input : default_value;
    }
  })
  .filter('trimDecimal', function() {
    // Trims the decimal to a whole number if all decimal places are 0
    return function(input) {
      if (isNaN(parseFloat(input))) {
        return input;
      }
      else if (input % 1 === 0) {
        return Math.round(input);
      }
      else {
        return input;
      }
    }
  })

  .config(function($interpolateProvider, $httpProvider, $resourceProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $resourceProvider.defaults.stripTrailingSlashes = false;
  })

  .run(function(editableOptions) {
    editableOptions.theme = 'bs3'; // bootstrap3 theme. Can be also 'bs2', 'default'
  })

})();
