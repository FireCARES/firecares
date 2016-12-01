'use strict';

(function() {
  angular.module('fireStation.departmentDetailController.userAdmin', [])
    .controller('userAdminController', UserAdminController);

  UserAdminController.$inject = ['$scope', 'limitToFilter', '$http', '$timeout'];

  function UserAdminController($scope, limitToFilter, $http, $timeout) {
    $scope.users = users;
    $scope.toadd = null;

    $scope.autocompleteUsers = function(username) {
      return $http.get("/autocomplete/UserAutocomplete/?q=" + username).then(function(response){
        var r = /data-value="(\d+)">(\w+)/g;
        var resp = [];
        var match = r.exec(response.data);
        while (match !== null) {
          var username = match[2];
          if (_.isEmpty(_.filter($scope.users, {username: username})) && username !== 'AnonymousUser') {
            resp.push(username);
          }
          match = r.exec(response.data);
        }
        return limitToFilter(resp, 15);
      });
    };

    $scope.deletePerms = function(user) {
      $scope.users.splice($scope.users.indexOf(user), 1);
    };

    $scope.addUser = function() {
      if (!$scope.toadd) {
        $scope.toadd = {
          id: null,
          username: '',
          can_change: false,
          can_admin: false
        };
        $timeout(function() {
          angular.element('input[name="username"]').focus();
        });
      }
    };

    $scope.cancelAdd = function() {
      $scope.toadd = null;
    };

    $scope.addComplete = function() {
      $scope.users.push($scope.toadd);
      $scope.toadd = null;
    };
  }
})();
