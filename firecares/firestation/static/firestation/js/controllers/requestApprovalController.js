'use strict';

(function() {
  angular.module('fireStation.requestApproval', [])
    .controller('requestApprovalController', RequestApprovalController);

  RequestApprovalController.$inject = ['$scope', '$http'];

  function RequestApprovalController($scope, $http) {
    $scope.requests = window.requests;

    $scope.update = function(request, approve) {
      $http.post('/accounts/verify-association-request/', {'id': request.id, 'approve': approve, 'message': request.message})
        .then(function successCallback(response) {
          var idx = _.findIndex($scope.requests, function(e) {
            return e.id == response.data.id
          });
          $scope.requests[idx] = response.data;
        }, function errorCallback(response) {

        });
    };
  }
})();
