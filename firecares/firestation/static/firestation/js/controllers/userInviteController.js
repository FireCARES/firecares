'use strict';

(function() {
  angular.module('fireStation.departmentDetailController.userInvite', [])
    .controller('userInviteController', UserInviteController);

  UserInviteController.$inject = ['$scope', '$http', '$timeout'];

  function UserInviteController($scope, $http, $timeout) {
    $scope.success = null;
    $scope.error = null;
    $scope.toInvite = null;
    $scope.invitations = invites;

    $scope.invite = function(email) {
      $http.post("/invitations/send-json-invite/", [{email: $scope.toInvite, department_id: config.id}]).then(function success(response) {
        $scope.error = null;
        $scope.success = 'Invitation sent to ' + $scope.toInvite;
        $scope.toInvite = null;
        $timeout(function() {
          $scope.success = null;
        }, 5000);
      }, function error(response) {
        if (response.data.invalid) {
          var msg = response.data.invalid[0][$scope.toInvite];
          $scope.success = null;
          $scope.error = msg;
          $timeout(function() {
            $scope.error = null;
          }, 5000);
        }
      });
    };
  }
})();
